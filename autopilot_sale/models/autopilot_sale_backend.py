import logging
from contextlib import contextmanager
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.autopilot import cron, tools
from odoo.addons.queue_job import identity_exact

_logger = logging.getLogger(__name__)


class AutopilotSaleBackend(models.Model):
    """A trading partner exchanging sale documents as files.

    The engine is the mechanism. The format belongs to a dialect, which adds a
    ``dialect`` value and, by ``_inherit``:

    * ``_<dialect>_import_order(file)``: stages a file's orders.
    * ``autopilot_sale.order._<dialect>_create_order()``: builds one.
    * ``autopilot_sale.order._<dialect>_acknowledge()``
    * ``autopilot_sale.picking._<dialect>_export()`` and
      ``autopilot_sale.invoice._<dialect>_export()``
    * ``_<dialect>_compute_supports_<flow>()``: opts into a flow. Without it,
      the flow is off.
    """

    _name = "autopilot_sale.backend"
    _description = "Sale EDI Backend"
    # utm.mixin: given to every imported order (autopilot_sale.order._apply_utm).
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

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        tracking=True,
        help="Default customer for imported orders.",
    )
    cleanup_enabled = fields.Boolean(
        string="Clean Up Stored Content",
        default=True,
        help="Clear the stored copy of finished imports once older than the "
        "period below. Anything not done keeps its copy, for a retry.",
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
        help="Fail on Error: a refused confirmation fails the order and keeps "
        "nothing, ready to retry. Keep Quotation on Error: a refusal leaves a "
        "quotation, with the reason posted on it and on this backend.",
    )

    # Groups, not users: record rules can only key off groups. Users, not
    # groups, to notify: followers are partners.
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
        help="Followers of this backend: they hear about imports, errors and "
        "documents sent.",
    )

    dialect = fields.Selection(
        selection=[],
        required=True,
        tracking=True,
        help="The trading partner's document format.",
    )

    supports_import_order = fields.Boolean(compute="_compute_supports_import_order")
    supports_ack = fields.Boolean(compute="_compute_supports_ack")
    supports_asn = fields.Boolean(compute="_compute_supports_asn")
    supports_invoice = fields.Boolean(compute="_compute_supports_invoice")

    # Kept in step by autopilot.mixin. Acks have no cron; the order job queues
    # them.
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
        "autopilot.connection",
        ondelete="restrict",
        tracking=True,
        help="Where files are read and written; each flow has its own path. "
        "Empty turns every transfer off.",
    )

    order_import_path = fields.Char(
        string="Orders Source Path",
        help="Glob of the order files to pick up, e.g. /in/ypo/*.csv (** "
        "recurses). May use {datetime:%Y}-style tokens; not {record.*}.",
    )
    order_import_processed_path = fields.Char(
        string="Orders Processed Path",
        help="Folder picked-up files are moved into, so they are read once, "
        "e.g. /in/ypo/processed/{datetime:%Y}/{datetime:%m}.",
    )
    ack_export_path = fields.Char(
        string="Acknowledgement Path",
        help="Full path, filename included. {record.*} is the sale order, "
        "{datetime:FORMAT} the current time; keep it unique or files "
        "overwrite. E.g. /out/ypo/ack/{record.name}-{datetime:%Y%m%dT%H%M%S}.csv",
    )
    asn_export_path = fields.Char(
        string="Dispatch Note Path",
        help="As the Acknowledgement Path, with {record.*} the picking.",
    )
    invoice_export_path = fields.Char(
        string="Invoice Path",
        help="As the Acknowledgement Path, with {record.*} the invoice.",
    )

    # One channel per flow, so e.g. imports can be preferred over acks.
    order_import_channel = fields.Char(
        string="Orders Channel",
        help="Job channel for files and orders, e.g. root.edi.orders. Empty "
        "uses root; an unconfigured channel runs under its nearest parent.",
    )
    ack_channel = fields.Char(
        string="Acknowledgements Channel",
        help="Job channel for acknowledgements, e.g. root.edi.acks.",
    )
    asn_channel = fields.Char(
        string="Dispatch Notes Channel",
        help="Job channel for dispatch notes, e.g. root.edi.asns.",
    )
    invoice_channel = fields.Char(
        string="Invoices Channel",
        help="Job channel for invoices, e.g. root.edi.invoices.",
    )

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
        """Archived backends too."""
        backends = self.with_context(active_test=False).search(
            [("cleanup_enabled", "=", True)]
        )
        for backend in backends:
            backend._cleanup()

    def _cleanup(self):
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
        """Required, not derived from the glob: where picked-up files go is a
        decision."""
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
        """Every Sale EDI job is queued through here."""
        self.ensure_one()
        options = {"identity_key": identity_exact}
        channel = (channel or "").strip()
        if channel:
            options["channel"] = channel
        return records.with_delay(**options)

    def _sweep_orders(self):
        """Move the matching files into the processed folder and return their
        new paths. The move is the claim, so an overlapping poll never reads a
        file twice."""
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
        """Yield ``(handle, target)`` to write at the rendered ``template``.
        ``target`` is the path written, for naming an audit copy::

            with backend._place(backend.asn_export_path, record=picking) as (
                fh,
                target,
            ):
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
        """The file record, not the backend, is queued, so a failure shows on
        the file where a sales user can retry it."""
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
        """A picking's binding is its sent marker."""
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
