import json
import logging
from contextlib import contextmanager

import fsspec

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.autopilot import cron
from odoo.addons.autopilot import tools as etl
from odoo.addons.queue_job import identity_exact

_logger = logging.getLogger(__name__)

# The sentinel provider meaning "no external endpoint". A real fsspec protocol
# is never named this, so a single equality test disables the backend.
_TRANSPORT_DISABLED = "disabled"


class AutopilotSaleBackend(models.Model):
    """A sale-EDI trading endpoint.

    The engine is deliberately thin. It owns only the *mechanism* every sale
    connector shares: a schedule (three crons), the fsspec transports, and a
    place to read/write files. Each cron simply **delegates to a dialect
    method** - ``getattr(self, "_<dialect>_import_orders")`` and friends - and is
    a no-op (logged) when the dialect does not implement it.

    Everything else is the dialect's job, and it owns it *completely*: a bridge
    module adds a ``dialect`` selection value and, by ``_inherit``, the
    ``_<dialect>_*`` methods that read the file(s), create the orders and
    bindings, and render + place any acknowledgement / dispatch note / invoice.
    The engine does not create orders, persist bindings, or render anything - it
    just claims inbound files (``_sweep_orders``) and hands the dialect somewhere
    to put its output (``_place``). The bindings are plain storage the dialect
    fills.

    A dialect need not implement every flow: a pure importer defines only
    ``_<dialect>_import_orders``. Acknowledgement is part of importing (the
    dialect calls its own ``_<dialect>_export_acks`` from within its import);
    dispatch notes and invoices are their own crons.
    """

    _name = "autopilot_sale.backend"
    _description = "Sale EDI Backend"
    _inherit = ["mail.thread", "autopilot.mixin"]

    name = fields.Char(required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)

    # Default customer imported orders are placed/billed against. A dialect may
    # resolve a different partner per file; this is the fallback.
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        tracking=True,
        help="Default customer imported orders are placed against.",
    )

    # Access & notification. Access is group-based (the only thing record rules
    # can key off): empty ``restrict_group_ids`` leaves the normal ACLs in
    # force, listing groups narrows the backend *and its bindings* to their
    # members. ``notify_user_ids`` are people (followers can only be partners,
    # not groups), auto-subscribed so the backend's chatter reaches them.
    restrict_group_ids = fields.Many2many(
        "res.groups",
        "autopilot_sale_backend_group_rel",
        "backend_id",
        "group_id",
        string="Access Groups",
        help="Restrict this backend and its bindings to members of these "
        "security groups. Empty leaves the normal access rights in force.",
    )
    notify_user_ids = fields.Many2many(
        "res.users",
        "autopilot_sale_backend_user_rel",
        "backend_id",
        "user_id",
        string="Notified Users",
        help="Users subscribed as followers of this backend, so they receive "
        "its chatter notifications (imports, errors, documents sent).",
    )

    dialect = fields.Selection(
        selection=[],
        required=True,
        tracking=True,
        help="The trading partner's document format. Provided by a bridge module",
    )

    # Which flows the selected dialect supports - an explicit per-dialect opt-in
    # (``_<dialect>_compute_supports_<flow>``, defaulting to False when absent),
    # used to gate the crons, buttons and transport pages directly.
    supports_import_order = fields.Boolean(compute="_compute_supports_import_order")
    supports_ack = fields.Boolean(compute="_compute_supports_ack")
    supports_asn = fields.Boolean(compute="_compute_supports_asn")
    supports_invoice = fields.Boolean(compute="_compute_supports_invoice")

    # Backing cron records, created and kept in step by autopilot. (Ack has no
    # cron - it rides the import.)
    order_import_cron_id = fields.Many2one("ir.cron", copy=False, readonly=True)
    asn_cron_id = fields.Many2one("ir.cron", copy=False, readonly=True)
    invoice_cron_id = fields.Many2one("ir.cron", copy=False, readonly=True)

    order_binding_ids = fields.One2many(
        "autopilot_sale.order", "backend_id", string="Orders"
    )
    order_count = fields.Integer(compute="_compute_counts")
    picking_binding_ids = fields.One2many(
        "autopilot_sale.picking", "backend_id", string="Dispatch Notes"
    )
    picking_count = fields.Integer(compute="_compute_counts")
    invoice_binding_ids = fields.One2many(
        "autopilot_sale.invoice", "backend_id", string="Invoices"
    )
    invoice_count = fields.Integer(compute="_compute_counts")

    provider = fields.Selection(
        selection="_provider_selection",
        default=_TRANSPORT_DISABLED,
        required=True,
        help="The single fsspec endpoint (local/SFTP/object store) this backend "
        "reads from and writes to. Each flow has its own path on it.",
    )
    storage_options = fields.Text(
        help="Optional JSON passed to fsspec as the provider's keyword arguments "
        "(e.g. SFTP host/credentials). Empty for a plain local filesystem.",
    )

    order_import_path = fields.Char(
        string="Orders Source Path",
        help="Glob matching the inbound order files to claim on the provider, "
        "e.g. /in/ypo/*.csv (** recurses into subfolders). May use "
        "{datetime:%Y} / {datetime:%m} / ... tokens (current time) to scope by "
        "date; no {record.*} token is available here, since files are claimed "
        "before any order exists.",
    )
    order_import_processed_path = fields.Char(
        string="Orders Processed Path",
        help="Absolute folder the claimed files are moved into so a poll does "
        "not re-read them, e.g. /in/ypo/processed/{datetime:%Y}/{datetime:%m}. "
        "May use {datetime:...} tokens. Empty archives to a 'processed' "
        "subfolder of the source.",
    )
    ack_export_path = fields.Char(
        string="Acknowledgement Path",
        help="Absolute destination path, INCLUDING the filename, each "
        "acknowledgement is written to. Supports template tokens: "
        "{datetime:FORMAT} - current time, e.g. {datetime:%Y-%m-%dT%H-%M-%S} - "
        "and {record.FIELD} - here the sale order, e.g. {record.name}. Make it "
        "unique per document (include {record.id} or {datetime}) or files "
        "overwrite. E.g. /out/ypo/ack/{record.name}-{datetime:%Y%m%dT%H%M%S}.csv",
    )
    asn_export_path = fields.Char(
        string="Dispatch Note Path",
        help="Absolute destination path (including the filename) each dispatch "
        "note is written to. Same tokens as the Acknowledgement Path, with "
        "{record.*} being the picking (e.g. {record.name}); include "
        "{record.id}/{datetime} to keep it unique.",
    )
    invoice_export_path = fields.Char(
        string="Invoice Path",
        help="Absolute destination path (including the filename) each invoice "
        "is written to. Same tokens as the Acknowledgement Path, with "
        "{record.*} being the invoice / account.move (e.g. {record.name}); "
        "include {record.id}/{datetime} to keep it unique.",
    )

    # A dialect opts into a flow by defining ``_<dialect>_compute_supports_<flow>``
    # (returning truthy); absent that method the flow is off.
    @api.depends("dialect")
    def _compute_supports_import_order(self):
        for backend in self:
            method = getattr(
                backend, f"_{backend.dialect}_compute_supports_import_order", None
            )
            backend.supports_import_order = bool(method()) if method else False

    @api.depends("dialect")
    def _compute_supports_ack(self):
        for backend in self:
            method = getattr(backend, f"_{backend.dialect}_compute_supports_ack", None)
            backend.supports_ack = bool(method()) if method else False

    @api.depends("dialect")
    def _compute_supports_asn(self):
        for backend in self:
            method = getattr(backend, f"_{backend.dialect}_compute_supports_asn", None)
            backend.supports_asn = bool(method()) if method else False

    @api.depends("dialect")
    def _compute_supports_invoice(self):
        for backend in self:
            method = getattr(
                backend, f"_{backend.dialect}_compute_supports_invoice", None
            )
            backend.supports_invoice = bool(method()) if method else False

    def _compute_counts(self):
        for model, field in (
            ("autopilot_sale.order", "order_count"),
            ("autopilot_sale.picking", "picking_count"),
            ("autopilot_sale.invoice", "invoice_count"),
        ):
            counts = dict(
                self.env[model]._read_group(
                    [("backend_id", "in", self.ids)],
                    groupby=["backend_id"],
                    aggregates=["__count"],
                )
            )
            for backend in self:
                backend[field] = counts.get(backend, 0)

    @api.model_create_multi
    def create(self, vals_list):
        backends = super().create(vals_list)
        backends._subscribe_notified_users()
        return backends

    def write(self, vals):
        result = super().write(vals)
        if "notify_user_ids" in vals:
            self._subscribe_notified_users()
        return result

    def _subscribe_notified_users(self):
        """Keep the notified users as followers so the backend's chatter reaches
        them. Called on create and whenever the set changes; message_subscribe
        is idempotent, so re-running it after a write is safe."""
        for backend in self:
            partners = backend.notify_user_ids.partner_id
            if partners:
                backend.message_subscribe(partner_ids=partners.ids)

    @api.model
    def _provider_selection(self):
        return [(_TRANSPORT_DISABLED, "Disabled")] + etl.files.fsspec_providers()

    @api.constrains("provider")
    def _check_provider(self):
        """The provider is only usable if fsspec can import its backing package.
        The selection offers every known protocol, so this is where a pick like
        SFTP-without-paramiko is rejected with fsspec's install hint."""
        for backend in self:
            if backend.provider == _TRANSPORT_DISABLED:
                continue
            try:
                fsspec.get_filesystem_class(backend.provider)
            except (ImportError, ValueError) as exc:
                raise ValidationError(
                    self.env._(
                        "The '%(provider)s' provider is not available: %(error)s",
                        provider=backend.provider,
                        error=exc,
                    )
                ) from exc

    def _fs(self):
        """The single fsspec filesystem for this backend's provider. fsspec
        unifies local/SFTP/object stores behind one API, so every flow stays
        transport-agnostic - they differ only by path."""
        self.ensure_one()
        try:
            options = json.loads(self.storage_options or "{}")
        except ValueError as exc:
            raise UserError(
                self.env._("Storage Options is not valid JSON: %s", exc)
            ) from exc
        if not isinstance(options, dict):
            raise UserError(self.env._("Storage Options must be a JSON object."))
        return fsspec.filesystem(self.provider, **options)

    def _render_path(self, template, record=None):
        """Resolve a configured path ``template`` with ``str.format`` against
        ``datetime`` (now) and ``record`` (optional), so any configured path can
        be date-partitioned or record-scoped, e.g.
        ``/out/{record.type}/{datetime:%Y}/{record.id}.xml`` or an inbound
        ``/in/{datetime:%Y-%m-%d}``. Shared by the inbound source/processed
        paths and the outbound _place targets."""
        self.ensure_one()
        return (template or "").format(datetime=fields.Datetime.now(), record=record)

    def _sweep_orders(self):
        """Claim every ``*.csv`` on the order source by moving it into the
        processed folder, and return the archived paths. Moving is the claim: a
        file is taken out of the scanned folder the moment it is picked up, so an
        overlapping poll can never read it twice. This is the engine's whole
        contribution to import - the dialect reads and parses the returned
        paths itself. Both source and processed paths are rendered
        (:meth:`_render_path`), so the processed folder can be date-partitioned."""
        self.ensure_one()
        if self.provider == _TRANSPORT_DISABLED:
            return []
        if not self.order_import_path:
            return []
        fs = self._fs()
        processed = self._render_path(self.order_import_processed_path)
        return etl.files.sweep(fs, f"{processed}/*.csv")

    @contextmanager
    def _place(self, template, record=None):
        """Open a writable handle at ``template`` on the provider and yield
        ``(handle, target)`` - the handle and the resolved destination path.

        ``template`` is the full destination path *including the filename* - one
        configured value - rendered by :meth:`_render_path` (so it may carry
        ``{datetime}`` / ``{record.*}`` tokens). Uniqueness is the template's
        responsibility: include ``{record.id}``/``{datetime}`` or files
        overwrite. ``target`` is handed back so a caller can name an audit copy
        after the file actually written.

            path = backend.asn_export_path
            with backend._place(path, record=picking) as (fh, target):
                etl.csv.write_rows(fh, rows, fieldnames=FIELDS)
        """
        self.ensure_one()
        target = self._render_path(template, record)
        with etl.files.opened(self._fs(), target) as handle:
            yield handle, target

    @cron(
        "order_import_cron_id",
        interval_number=15,
        interval_type="minutes",
        active=lambda backend: (
            backend.active
            and backend.supports_import_order
            and backend.provider != _TRANSPORT_DISABLED
        ),
    )
    def _import_orders(self):
        """Claim inbound files and hand each to the dialect as its own queued
        job. Claiming (the fsspec move) happens here in the cron transaction;
        reading/parsing/creating is the dialect's ``_<dialect>_import_orders(path)``,
        one job per file so each retries independently."""
        self.ensure_one()
        for path in self.with_delay()._sweep_orders():
            self.with_delay(identity_key=identity_exact)._import_order(path)

    def _import_order(self, path):
        self.ensure_one()
        if not self.supports_import_order:
            _logger.info(
                "Sale EDI %s: dialect %r imports no orders; skipping.",
                self.name,
                self.dialect,
            )
            return
        return getattr(self, f"_{self.dialect}_import_order")(path)

    @cron(
        "asn_cron_id",
        interval_number=15,
        interval_type="minutes",
        active=lambda backend: (
            backend.active
            and backend.supports_asn
            and backend.provider != _TRANSPORT_DISABLED
        ),
    )
    def _export_asns(self):
        """Bind every not-yet-bound customer-facing done picking on a bound
        order and export its dispatch note. Eligibility is generic; the render
        is the dialect's ``autopilot_sale.picking._<dialect>_export``."""
        self.ensure_one()
        if not self.supports_asn:
            _logger.info(
                "Sale EDI %s: dialect %r sends no dispatch notes; skipping.",
                self.name,
                self.dialect,
            )
            return
        Binding = self.env["autopilot_sale.picking"]
        for picking in self.env["stock.picking"].search(self._asn_domain()):
            Binding.create({"backend_id": self.id, "odoo_id": picking.id}).with_delay(
                identity_key=identity_exact
            )._export()

    def _asn_domain(self):
        """Customer-facing done pickings on an order bound to this backend, not
        yet bound themselves (the binding's existence is the sent marker)."""
        self.ensure_one()
        return [
            ("state", "=", "done"),
            ("picking_type_id.code", "=", "outgoing"),
            ("location_dest_id.usage", "=", "customer"),
            ("sale_id.autopilot_sale_binding_ids.backend_id", "=", self.id),
            ("autopilot_sale_binding_ids", "not any", [("backend_id", "=", self.id)]),
        ]

    @cron(
        "invoice_cron_id",
        interval_number=15,
        interval_type="minutes",
        active=lambda backend: (
            backend.active
            and backend.supports_invoice
            and backend.provider != _TRANSPORT_DISABLED
        ),
    )
    def _export_invoices(self):
        """Bind every not-yet-bound posted customer invoice on a bound order and
        export it. Eligibility is generic; the render is the dialect's
        ``autopilot_sale.invoice._<dialect>_export``."""
        self.ensure_one()
        if not self.supports_invoice:
            _logger.info(
                "Sale EDI %s: dialect %r sends no invoices; skipping.",
                self.name,
                self.dialect,
            )
            return
        Binding = self.env["autopilot_sale.invoice"]
        for move in self.env["account.move"].search(self._invoice_domain()):
            Binding.create({"backend_id": self.id, "odoo_id": move.id}).with_delay(
                identity_key=identity_exact
            )._export()

    def _invoice_domain(self):
        self.ensure_one()
        return [
            ("move_type", "in", ("out_invoice", "out_refund")),
            ("state", "=", "posted"),
            (
                "invoice_line_ids.sale_line_ids.order_id"
                ".autopilot_sale_binding_ids.backend_id",
                "=",
                self.id,
            ),
            ("autopilot_sale_binding_ids", "not any", [("backend_id", "=", self.id)]),
        ]

    def action_import_orders(self):
        self.ensure_one()
        if not self.supports_import_order:
            raise UserError(
                self.env._("Dialect %r does not import orders.", self.dialect)
            )
        if self.provider == _TRANSPORT_DISABLED:
            raise UserError(self.env._("This backend has no provider configured."))
        self._import_orders()
        return self._notify(
            self.env._("Import run"),
            self.env._("Inbound order files have been imported."),
        )

    def action_export_asns(self):
        self.ensure_one()
        self._export_asns()
        return self._notify(
            self.env._("Dispatch notes run"),
            self.env._("Dispatched pickings have been processed."),
        )

    def action_export_invoices(self):
        self.ensure_one()
        self._export_invoices()
        return self._notify(
            self.env._("Invoices run"),
            self.env._("Posted invoices have been processed."),
        )

    def _notify(self, title, message):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": title,
                "message": message,
                "sticky": False,
            },
        }

    def _action_view(self, name, model):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "view_mode": "list,form",
            "domain": [("backend_id", "=", self.id)],
            "context": {"default_backend_id": self.id},
        }

    def action_view_orders(self):
        return self._action_view(self.env._("Orders"), "autopilot_sale.order")

    def action_view_pickings(self):
        return self._action_view(self.env._("Dispatch Notes"), "autopilot_sale.picking")

    def action_view_invoices(self):
        return self._action_view(self.env._("Invoices"), "autopilot_sale.invoice")
