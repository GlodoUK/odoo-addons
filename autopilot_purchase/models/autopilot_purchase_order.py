from odoo import api, fields, models

STATES = [
    ("to_send", "To Send"),
    ("pending", "Pending"),
    ("done", "Sent"),
    ("failed", "Failed"),
    ("cancelled", "Cancelled"),
]


class AutopilotPurchaseOrder(models.Model):
    """A purchase order bound to a backend when confirmed. One per backend
    and order, so the schedule only ever sends it once. Its state is To Send
    until a file holds it, then that of its latest file.
    """

    _name = "autopilot_purchase.order"
    _description = "Purchase EDI Order Binding"
    _order = "id desc"

    backend_id = fields.Many2one(
        "autopilot_purchase.backend",
        required=True,
        ondelete="cascade",
        index=True,
    )
    odoo_id = fields.Many2one(
        "purchase.order",
        string="Purchase Order",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="backend_id.company_id", store=True, index=True
    )
    file_ids = fields.Many2many(
        "autopilot_purchase.order.file",
        "autopilot_purchase_order_file_rel",
        "order_binding_id",
        "file_id",
        string="Files",
        readonly=True,
    )
    state = fields.Selection(
        STATES,
        compute="_compute_state",
        store=True,
        index=True,
    )
    external_values = fields.Serialized(
        help="Dialect-specific values that have no dedicated column.",
    )

    _unique_binding = models.Constraint(
        "unique(backend_id, odoo_id)",
        "This purchase order is already bound to this backend.",
    )

    @api.depends("file_ids.state")
    def _compute_state(self):
        for binding in self:
            binding.state = binding.file_ids.sorted("id")[-1:].state or "to_send"

    @api.depends("backend_id.name", "odoo_id.name")
    def _compute_display_name(self):
        for binding in self:
            binding.display_name = (
                f"{binding.backend_id.name or '?'}/{binding.odoo_id.name or '?'}"
            )

    def _send(self):
        File = self.env["autopilot_purchase.order.file"]
        files = File
        for backend in self.backend_id:
            bindings = self.filtered(lambda b, backend=backend: b.backend_id == backend)
            files |= File.create(
                [
                    {"backend_id": backend.id, "order_binding_ids": batch.ids}
                    for batch in backend._batch(bindings)
                    if batch
                ]
            )
        files._enqueue()
        return files

    def action_send_again(self):
        self.filtered(lambda b: b.state not in ("to_send", "pending"))._send()

    @api.model
    def _autopilot_activity_query(self):
        # No Retry here. A failed send is retried on its file.
        return self.env["autopilot.activity"]._source_select(
            self,
            backend="backend_id",
            company="company_id",
            state="state",
            status={
                "to_send": "draft",
                "pending": "pending",
                "done": "done",
                "failed": "error",
                "cancelled": "cancelled",
            },
        )
