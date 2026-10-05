import base64
import json
import logging

from odoo import api, fields, models
from odoo.exceptions import RedirectWarning, UserError

_logger = logging.getLogger(__name__)


class AutopilotSaleOrder(models.Model):
    """Per-(backend, sale order) binding: one order from an inbound file, from
    the moment it is staged until its sale order exists.

    Import is two jobs. The file job (``autopilot_sale.order.file``) has the
    dialect split the file into orders, staging one binding per order with its
    source rows in ``payload``; the engine then queues each binding as its own
    job (``_process``). So one bad order fails alone, and it can be retried
    alone, without re-reading the file.

    ``_process`` is create -> confirm -> queue the acknowledgement: the
    dialect's ``_<dialect>_create_order`` builds the sale order from the
    payload, the engine confirms it per the backend's ``confirm_policy``
    (``_confirm``), then queues ``_acknowledge`` as its own job on the ack
    channel. That job is created in the order job's transaction, so an ack is
    never sent for an order whose job rolls back.

    Generic references live in ``external_values`` (a ``fields.Serialized``
    catch-all); a bridge adds a typed column by ``_inherit`` for anything it
    lists/searches on.
    """

    _name = "autopilot_sale.order"
    _description = "Sale EDI Order Binding"
    _inherit = ["mail.thread", "autopilot_sale.job.mixin"]
    _order = "id desc"

    backend_id = fields.Many2one(
        "autopilot_sale.backend",
        required=True,
        ondelete="cascade",
        index=True,
    )
    # Empty while staged: the order job creates the sale order.
    odoo_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        ondelete="cascade",
        index=True,
    )
    file_id = fields.Many2one(
        "autopilot_sale.order.file",
        string="Source File",
        ondelete="set null",
        index=True,
        copy=False,
        help="The inbound file this order was imported from. Filled "
        "automatically (default_file_id in context) when a dialect creates "
        "this binding during an import job; blank otherwise.",
    )
    company_id = fields.Many2one(
        related="backend_id.company_id", store=True, index=True
    )
    line_ids = fields.One2many(
        "autopilot_sale.order.line", "order_binding_id", string="Lines"
    )

    external_ref = fields.Char(
        string="External Reference",
        index=True,
        help="The trading partner's identifier for this order.",
    )
    external_values = fields.Serialized(
        help="Dialect-specific captured values that have no dedicated column.",
    )
    payload = fields.Binary(
        attachment=True,
        copy=False,
        help="This order's rows from the inbound file (JSON), staged by the "
        "file import and read by the order job. Cleared once the order is "
        "done and older than its backend's clean-up period.",
    )

    _unique_binding = models.Constraint(
        "unique(backend_id, odoo_id)",
        "This order is already bound to this backend.",
    )

    @api.depends("backend_id.name", "odoo_id.name", "external_ref")
    def _compute_display_name(self):
        for binding in self:
            binding.display_name = (
                f"{binding.backend_id.name or '?'}/"
                f"{binding.odoo_id.name or binding.external_ref or '?'}"
            )

    # ------------------------------------------------------------------
    # Payload
    # ------------------------------------------------------------------
    @api.model
    def _encode_payload(self, data):
        """``data`` (anything JSON-serialisable, typically the order's rows)
        as a ``payload`` value."""
        return base64.b64encode(json.dumps(data).encode())

    def _read_payload(self):
        self.ensure_one()
        raw = self.with_context(bin_size=False).payload
        if not raw:
            raise UserError(
                self.env._("%s has no payload to process.", self.display_name)
            )
        return json.loads(base64.b64decode(raw))

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------
    def _enqueue(self):
        """Queue each binding's order job (see ``autopilot_sale.job.mixin``)."""
        self._queue("_process", "order_import_channel")

    def _requeue(self):
        self._enqueue()

    def _process(self):
        """The order job: see :meth:`_build`."""
        self._run(self._build)

    def _build(self):
        """Create -> confirm -> queue the ack for one staged order (see the
        class docstring). Re-running it on a binding that already has its order
        skips the create."""
        self.ensure_one()
        if not self.odoo_id:
            dialect = self.backend_id.dialect
            method = getattr(self, f"_{dialect}_create_order", None)
            if not method:
                raise UserError(self.env._("Dialect %r cannot create orders.", dialect))
            method()
            self._apply_utm()
        self._confirm()
        backend = self.backend_id
        if backend.supports_ack and backend.connection_id:
            # Its own job, on its own channel. Queued in this transaction, so
            # it is rolled back with the order if this job fails. Without a
            # connection (an upload-only backend) there is nowhere to send it.
            backend._delay(self, backend.ack_channel)._acknowledge()

    def _apply_utm(self):
        """The backend's UTM values on the new sale order, wherever the dialect
        left them empty."""
        order, backend = self.odoo_id, self.backend_id
        vals = {
            name: backend[name].id
            for _param, name, _cookie in self.env["utm.mixin"].tracking_fields()
            if backend[name] and not order[name]
        }
        if vals:
            order.write(vals)

    def _confirm(self):
        """Confirm each quotation per its backend's ``confirm_policy``:

        * ``draft`` - leave it.
        * ``confirm`` - confirm; a refusal fails the order, rolling it back
          (retry once the cause is fixed).
        * ``confirm_or_draft`` - confirm inside a savepoint; a refusal rolls
          back only the confirmation and leaves a quotation with a note.

        Only business refusals (``UserError``/``RedirectWarning``) are
        recovered; anything else (e.g. a serialization failure) reaches
        queue_job for its own retry. ``action_confirm`` can also refuse
        without raising (returning a wizard), so the state is checked after."""
        for binding in self:
            order = binding.odoo_id
            policy = binding.backend_id.confirm_policy
            if policy == "draft" or order.state not in ("draft", "sent"):
                continue
            if policy == "confirm":
                binding._confirm_order()
                continue
            try:
                with self.env.cr.savepoint():
                    binding._confirm_order()
            except (UserError, RedirectWarning) as exc:
                binding._on_confirm_failed(exc)

    def _confirm_order(self):
        self.ensure_one()
        order = self.odoo_id
        order.action_confirm()
        if order.state != "sale":
            raise UserError(
                self.env._("%s was not confirmed by action_confirm.", order.name)
            )

    def _on_confirm_failed(self, exc):
        """Note a recovered confirmation failure where people will see it: on
        the quotation, and on the backend (whose Notified Users follow it)."""
        self.ensure_one()
        reason = exc.args[0] if exc.args else str(exc)
        body = self.env._(
            "Automatic confirmation of %(order)s failed; it was left as a "
            "quotation: %(reason)s",
            order=self.odoo_id.name,
            reason=reason,
        )
        _logger.info("Sale EDI %s: %s", self.backend_id.name, body)
        self.odoo_id.message_post(body=body)
        self.backend_id.message_post(body=body)

    def _acknowledge(self):
        """Acknowledge each order via its dialect's ``_<dialect>_acknowledge``
        (a no-op, logged, for a dialect that does not acknowledge - e.g. a pure
        importer). The dialect renders and places the file, reaching the ack
        path through ``self.backend_id._place(backend.ack_export_path, ...)``."""
        for binding in self:
            method = getattr(
                binding, f"_{binding.backend_id.dialect}_acknowledge", None
            )
            if not method:
                _logger.info(
                    "Sale EDI: dialect %r does not acknowledge; skipping %s.",
                    binding.backend_id.dialect,
                    binding.display_name,
                )
                continue
            method()
