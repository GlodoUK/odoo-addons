import logging
from contextlib import contextmanager
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.autopilot import cron, tools
from odoo.addons.queue_job import identity_exact

_logger = logging.getLogger(__name__)


class AutopilotSaleBackend(models.Model):
    """A sale-EDI trading endpoint.

    The engine owns the *mechanism* every sale connector shares: the schedules
    (order import, dispatch notes, invoices), the connection, the inbound
    files and their per-order jobs (``autopilot_sale.order.file`` ->
    ``autopilot_sale.order``), confirmation, job channels and housekeeping.
    The **format** is the dialect's: a bridge module adds a ``dialect``
    selection value and, by ``_inherit``, convention-named methods -
    ``_<dialect>_import_order(file)`` staging a file's orders,
    ``autopilot_sale.order._<dialect>_create_order`` building one,
    ``_<dialect>_acknowledge`` and ``autopilot_sale.picking/invoice.
    _<dialect>_export`` rendering what goes back. A dialect opts into each
    flow with ``_<dialect>_compute_supports_<flow>``; the rest stay off.
    """

    _name = "autopilot_sale.backend"
    _description = "Sale EDI Backend"
    # utm.mixin: the campaign / source / medium given to every order imported
    # here (see autopilot_sale.order._apply_utm).
    _inherit = ["mail.thread", "autopilot.mixin", "utm.mixin"]

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
    # Housekeeping: how long finished imports keep their stored content.
    cleanup_enabled = fields.Boolean(
        string="Clean Up Stored Content",
        default=True,
        help="Clear the stored copy of imported files and the staged rows of "
        "imported orders once they are done and older than the period below. "
        "Pending, failed and cancelled ones keep theirs, for a retry.",
    )
    cleanup_days = fields.Integer(string="Keep For (days)", default=30)
    confirm_policy = fields.Selection(
        [
            ("draft", "Leave as Quotation"),
            ("confirm", "Confirm, Fail on Error"),
            ("confirm_or_draft", "Confirm, Keep Quotation on Error"),
        ],
        string="Confirmation",
        default="draft",
        required=True,
        tracking=True,
        help="What happens to each imported order once created. Leave as "
        "Quotation: nothing. Confirm, Fail on Error: confirm it; if "
        "confirmation is refused the order fails and nothing is kept, "
        "ready to retry once the cause is fixed. Confirm, Keep Quotation on "
        "Error: confirm it; if refused, keep it as a quotation and post the "
        "reason on it and on this backend.",
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

    order_file_ids = fields.One2many(
        "autopilot_sale.order.file", "backend_id", string="Order Files"
    )
    order_file_count = fields.Integer(compute="_compute_counts")
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

    connection_id = fields.Many2one(
        "autopilot_sale.connection",
        ondelete="restrict",
        tracking=True,
        help="The endpoint (local/SFTP/object store) this backend reads from "
        "and writes to; each flow has its own path on it. Empty disables every "
        "transport. Several backends can share one connection.",
    )

    order_import_path = fields.Char(
        string="Orders Source Path",
        help="Glob matching the inbound order files to claim on the connection, "
        "e.g. /in/ypo/*.csv (** recurses into subfolders). May use "
        "{datetime:%Y} / {datetime:%m} / ... tokens (current time) to scope by "
        "date; no {record.*} token is available here, since files are claimed "
        "before any order exists.",
    )
    order_import_processed_path = fields.Char(
        string="Orders Processed Path",
        help="Absolute folder the claimed files are moved into so a poll does "
        "not re-read them, e.g. /in/ypo/processed/{datetime:%Y}/{datetime:%m}. "
        "May use {datetime:...} tokens. Required once a source is set: where "
        "claimed files go is not something to infer from a glob.",
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

    # Job channels, one per operation, so e.g. importing orders can be
    # preferred over sending acknowledgements. Empty passes no channel.
    order_import_channel = fields.Char(
        string="Orders Channel",
        help="queue_job channel the order import jobs (the file and each "
        "order) run on, e.g. root.edi.orders. Empty uses root. A channel "
        "missing from the queue_job channels config runs under its nearest "
        "configured parent.",
    )
    ack_channel = fields.Char(
        string="Acknowledgements Channel",
        help="queue_job channel the acknowledgement jobs run on, e.g. "
        "root.edi.acks. Empty uses root. A channel missing from the "
        "queue_job channels config runs under its nearest configured "
        "parent.",
    )
    asn_channel = fields.Char(
        string="Dispatch Notes Channel",
        help="queue_job channel the dispatch note jobs run on, e.g. "
        "root.edi.asns. Empty uses root. A channel missing from the "
        "queue_job channels config runs under its nearest configured "
        "parent.",
    )
    invoice_channel = fields.Char(
        string="Invoices Channel",
        help="queue_job channel the invoice jobs run on, e.g. "
        "root.edi.invoices. Empty uses root. A channel missing from the "
        "queue_job channels config runs under its nearest configured "
        "parent.",
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
            ("autopilot_sale.order.file", "order_file_count"),
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

    @api.constrains("cleanup_enabled", "cleanup_days")
    def _check_cleanup_days(self):
        for backend in self:
            if backend.cleanup_enabled and backend.cleanup_days < 1:
                raise ValidationError(
                    self.env._(
                        "Backend %s must keep content for at least a day.", backend.name
                    )
                )

    @api.model
    def _cron_cleanup(self):
        """Daily: clean up every backend that has it enabled, archived ones
        too."""
        backends = self.with_context(active_test=False).search(
            [("cleanup_enabled", "=", True)]
        )
        for backend in backends:
            backend._cleanup()

    def _cleanup(self):
        """Clear the stored content of this backend's finished imports older
        than its period: each file's copy and each order's payload, once
        done."""
        self.ensure_one()
        cutoff = fields.Datetime.now() - timedelta(days=self.cleanup_days)
        files = self.env["autopilot_sale.order.file"].search(
            [
                ("backend_id", "=", self.id),
                ("create_date", "<", cutoff),
                ("data", "!=", False),
                ("state", "=", "done"),
            ]
        )
        files.data = False
        orders = self.env["autopilot_sale.order"].search(
            [
                ("backend_id", "=", self.id),
                ("create_date", "<", cutoff),
                ("state", "=", "done"),
                ("payload", "!=", False),
            ]
        )
        orders.payload = False
        _logger.info(
            "Sale EDI %s: cleared %s file(s) and %s order payload(s).",
            self.name,
            len(files),
            len(orders),
        )

    @api.constrains("order_import_path", "order_import_processed_path")
    def _check_order_import_paths(self):
        """A source to poll needs somewhere to put what it claims. Required
        rather than derived: :func:`~odoo.addons.autopilot.tools.files.archive`
        moves a file *out* of the polled folder, and the destination for that is
        a decision, not something to guess from the source glob."""
        for backend in self:
            if backend.order_import_path and not backend.order_import_processed_path:
                raise ValidationError(
                    self.env._(
                        "Backend %s has an Orders Source Path, so it needs an "
                        "Orders Processed Path.",
                        backend.name,
                    )
                )

    def _delay(self, records, channel=None):
        """``records.with_delay(...)``, on ``channel`` (one of this backend's
        ``*_channel`` fields) when it is set; otherwise no channel is passed, so
        queue_job's own default applies. Every Sale EDI job is queued through
        here."""
        self.ensure_one()
        options = {"identity_key": identity_exact}
        channel = (channel or "").strip()
        if channel:
            options["channel"] = channel
        return records.with_delay(**options)

    def _sweep_orders(self):
        """Claim every file matching the order source glob by moving it into the
        processed folder, and return the archived paths. Moving is the claim: a
        file is taken out of the scanned folder the moment it is picked up, so an
        overlapping poll can never read it twice. This is the engine's whole
        contribution to import - the dialect reads and parses the returned
        paths itself. Both source and processed paths are rendered
        (``tools.files.render_path``), so either can be date-scoped; both are required
        config (:meth:`_check_order_import_paths`), so neither is inferred
        here."""
        self.ensure_one()
        if not self.connection_id:
            return []
        if not self.order_import_path:
            return []
        return self.connection_id._sweep(
            tools.files.render_path(self.order_import_path),
            tools.files.render_path(self.order_import_processed_path),
        )

    @contextmanager
    def _place(self, template, record=None):
        """Open a writable handle at ``template`` on the connection and yield
        ``(handle, target)`` - the handle and the resolved destination path.

        ``template`` is the full destination path *including the filename* - one
        configured value - rendered by ``tools.files.render_path`` (so it may carry
        ``{datetime}`` / ``{record.*}`` tokens). Uniqueness is the template's
        responsibility: include ``{record.id}``/``{datetime}`` or files
        overwrite. ``target`` is handed back so a caller can name an audit copy
        after the file actually written.

            path = backend.asn_export_path
            with backend._place(path, record=picking) as (fh, target):
                etl.csv.write_rows(fh, rows, fieldnames=FIELDS)
        """
        self.ensure_one()
        target = tools.files.render_path(template, record)
        with self.connection_id._opened(target) as handle:
            yield handle, target

    @cron(
        "order_import_cron_id",
        interval_number=15,
        interval_type="minutes",
        active=lambda backend: (
            backend.active and backend.supports_import_order and backend.connection_id
        ),
    )
    def _import_orders(self):
        """Claim inbound files and hand each to the dialect as its own queued
        job. Claiming (the fsspec move) happens here in the cron transaction;
        reading/parsing/creating is the dialect's ``_<dialect>_import_order(file)``.

        Each claimed file becomes an ``autopilot_sale.order.file`` *before* it
        is queued, and that record - not the backend - is what gets delayed.
        That makes the file the job's origin record, so its state/error land
        on the file (via stored related fields) where a sales user can see a
        failure and pull it out of the queue, rather than only in the
        technical Job Queue."""
        self.ensure_one()
        File = self.env["autopilot_sale.order.file"]
        for path in self._sweep_orders():
            File.create(File._vals_from_connection(self, path))._enqueue()

    @cron(
        "asn_cron_id",
        interval_number=15,
        interval_type="minutes",
        active=lambda backend: (
            backend.active and backend.supports_asn and backend.connection_id
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
            binding = Binding.create({"backend_id": self.id, "odoo_id": picking.id})
            self._delay(binding, self.asn_channel)._export()

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
            backend.active and backend.supports_invoice and backend.connection_id
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
            binding = Binding.create({"backend_id": self.id, "odoo_id": move.id})
            self._delay(binding, self.invoice_channel)._export()

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
        if not self.connection_id:
            raise UserError(self.env._("This backend has no Connection."))
        self._import_orders()
        return self._notify(
            self.env._("Import run"),
            self.env._("Inbound order files have been imported."),
        )

    def action_upload_file(self):
        """Open the wizard importing a file by hand (no connection needed)."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Upload File"),
            "res_model": "autopilot_sale.upload.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_backend_id": self.id},
        }

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

    def action_view_files(self):
        return self._action_view(self.env._("Order Files"), "autopilot_sale.order.file")

    def action_view_orders(self):
        return self._action_view(self.env._("Orders"), "autopilot_sale.order")

    def action_view_pickings(self):
        return self._action_view(self.env._("Dispatch Notes"), "autopilot_sale.picking")

    def action_view_invoices(self):
        return self._action_view(self.env._("Invoices"), "autopilot_sale.invoice")
