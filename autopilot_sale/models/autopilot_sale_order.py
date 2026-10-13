import base64
import json
import logging

from odoo import api, fields, models
from odoo.exceptions import RedirectWarning, UserError

_logger = logging.getLogger(__name__)


class AutopilotSaleOrder(models.Model):
    """One imported order, from staging until its sale order exists.

    Its job builds the order (``_<dialect>_create_order``), confirms it per the
    backend's policy, then queues the acknowledgement. A dialect adds a typed
    column for any reference it lists or searches on; the rest go in
    ``external_values``.
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
    # Empty while staged.
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
        help="The file this order was imported from.",
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
        help="Partner values with no column of their own.",
    )
    payload = fields.Binary(
        attachment=True,
        copy=False,
        help="This order's rows from the file, as JSON. Cleared after the "
        "backend's clean-up period once done.",
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

    @api.model
    def _encode_payload(self, data):
        return base64.b64encode(json.dumps(data).encode())

    def _read_payload(self):
        self.ensure_one()
        raw = self.with_context(bin_size=False).payload
        if not raw:
            raise UserError(
                self.env._("%s has no payload to process.", self.display_name)
            )
        return json.loads(base64.b64decode(raw))

    def _enqueue(self):
        self._queue("_process", "order_import_channel")

    def _requeue(self):
        self._enqueue()

    def _process(self):
        self._run(self._build)

    def _build(self):
        """A retry skips the create once the order exists."""
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
            # Queued in this transaction, so no ack goes out for an order whose
            # job rolls back.
            backend._delay(self, backend.ack_channel)._acknowledge()

    def _apply_utm(self):
        """Only where the dialect left them empty."""
        order, backend = self.odoo_id, self.backend_id
        vals = {
            name: backend[name].id
            for _param, name, _cookie in self.env["utm.mixin"].tracking_fields()
            if backend[name] and not order[name]
        }
        if vals:
            order.write(vals)

    def _confirm(self):
        """Only business refusals (``UserError``, ``RedirectWarning``) are
        recovered. Anything else, such as a serialisation failure, is left to
        queue_job to retry. ``action_confirm`` can also refuse by returning a
        wizard, so the state is checked after."""
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
        """Posted on the backend too, so its Notified Users hear of it."""
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
