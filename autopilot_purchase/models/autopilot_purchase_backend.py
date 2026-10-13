import logging
from contextlib import contextmanager

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.autopilot import cron, tools
from odoo.addons.queue_job import identity_exact

_logger = logging.getLogger(__name__)


class AutopilotPurchaseBackend(models.Model):
    """Sends one vendor's confirmed purchase orders as files in their format.

    A dialect adds a ``dialect`` value plus
    ``autopilot_purchase.order.file._<dialect>_render()`` (the file's bytes)
    and, to put several orders in one file, ``_<dialect>_batch(bindings)``.
    """

    _name = "autopilot_purchase.backend"
    _description = "Purchase EDI Backend"
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
    partner_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        tracking=True,
        help="Orders confirmed to this vendor or its contacts are sent "
        "through this backend.",
    )
    restrict_group_ids = fields.Many2many(
        "res.groups",
        "autopilot_purchase_backend_group_rel",
        "backend_id",
        "group_id",
        string="Access Groups",
        help="Restrict this backend and its bindings to members of these "
        "security groups. Empty leaves the normal access rights in force.",
    )
    notify_user_ids = fields.Many2many(
        "res.users",
        "autopilot_purchase_backend_user_rel",
        "backend_id",
        "user_id",
        string="Notified Users",
        help="Follow this backend, so they hear about its activity.",
    )

    dialect = fields.Selection(
        selection=[],
        required=True,
        tracking=True,
        help="The vendor's file format.",
    )

    order_export_cron_id = fields.Many2one("ir.cron", copy=False, readonly=True)

    order_binding_ids = fields.One2many(
        "autopilot_purchase.order", "backend_id", string="Orders"
    )
    order_count = fields.Integer(compute="_compute_counts")
    order_file_ids = fields.One2many(
        "autopilot_purchase.order.file", "backend_id", string="Order Files"
    )
    order_file_count = fields.Integer(compute="_compute_counts")

    connection_id = fields.Many2one(
        "autopilot.connection",
        ondelete="restrict",
        tracking=True,
        help="Where order files are written. Empty pauses sending.",
    )
    order_export_path = fields.Char(
        string="Orders Path",
        help="Full path, filename included. {record.*} is the order file, so "
        "{record.purchase_order_ids[0].name} is its first order. "
        "{datetime:FORMAT} is the time. Keep it unique per file, or files "
        "overwrite each other. E.g. "
        "/out/ypo/orders/{record.id}-{datetime:%Y%m%dT%H%M%S}.csv",
    )
    order_export_channel = fields.Char(
        string="Orders Channel",
        help="Job channel for sending files, e.g. root.edi.purchase. Empty uses root.",
    )

    def _compute_counts(self):
        for model, field in (
            ("autopilot_purchase.order", "order_count"),
            ("autopilot_purchase.order.file", "order_file_count"),
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

    def _delay(self, records, channel=None):
        self.ensure_one()
        options = {"identity_key": identity_exact}
        channel = (channel or "").strip()
        if channel:
            options["channel"] = channel
        return records.with_delay(**options)

    @contextmanager
    def _place(self, template, record=None):
        """Yield ``(handle, target)`` for writing at the rendered
        ``template``."""
        self.ensure_one()
        if not self.connection_id:
            raise UserError(self.env._("Backend %s has no Connection.", self.name))
        if not template:
            raise UserError(self.env._("Backend %s has no Orders Path.", self.name))
        target = tools.files.render_path(template, record)
        with self.connection_id._opened(target) as handle:
            yield handle, target

    @cron(
        "order_export_cron_id",
        interval_number=15,
        interval_type="minutes",
        active=lambda backend: backend.active and backend.connection_id,
    )
    def _export_orders(self):
        """An order cancelled after binding waits; it goes if re-confirmed."""
        self.ensure_one()
        self.env["autopilot_purchase.order"].search(
            [
                ("backend_id", "=", self.id),
                ("state", "=", "to_send"),
                ("odoo_id.state", "=", "purchase"),
            ],
            order="id",
        )._send()

    @api.model
    def _bind(self, orders):
        """Bind confirmed ``orders`` to their vendor's backends. Runs as
        superuser, as the purchaser confirming may not see the backend."""
        Binding = self.env["autopilot_purchase.order"].sudo()
        vals_list = []
        for order in orders:
            backends = self.sudo().search(
                [
                    ("company_id", "=", order.company_id.id),
                    (
                        "partner_id.commercial_partner_id",
                        "=",
                        order.partner_id.commercial_partner_id.id,
                    ),
                ]
            )
            backends -= order.sudo().autopilot_purchase_binding_ids.backend_id
            vals_list += [
                {"backend_id": backend.id, "odoo_id": order.id} for backend in backends
            ]
        return Binding.create(vals_list)

    def _batch(self, bindings):
        """The recordsets that each become one file: the dialect's
        ``_<dialect>_batch(bindings)``, else one per order."""
        self.ensure_one()
        method = getattr(self, f"_{self.dialect}_batch", None)
        if method:
            return method(bindings)
        return list(bindings)

    def action_export_orders(self):
        self.ensure_one()
        if not self.connection_id:
            raise UserError(self.env._("This backend has no Connection."))
        self._export_orders()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": self.env._("Export run"),
                "message": self.env._("Orders to send have been queued."),
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
        return self._action_view(self.env._("Orders"), "autopilot_purchase.order")

    def action_view_files(self):
        return self._action_view(
            self.env._("Order Files"), "autopilot_purchase.order.file"
        )
