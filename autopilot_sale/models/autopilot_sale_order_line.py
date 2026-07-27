from odoo import api, fields, models


class AutopilotSaleOrderLine(models.Model):
    """Per-order-line binding: the trading partner's line-level references for
    one ``sale.order.line``, in a ``fields.Serialized`` catch-all (a bridge adds
    typed columns for any it lists/searches on)."""

    _name = "autopilot_sale.order.line"
    _description = "Sale EDI Order Line Binding"
    _order = "id"

    order_binding_id = fields.Many2one(
        "autopilot_sale.order",
        required=True,
        ondelete="cascade",
        index=True,
    )
    odoo_id = fields.Many2one(
        "sale.order.line",
        string="Order Line",
        required=True,
        ondelete="cascade",
        index=True,
    )
    backend_id = fields.Many2one(
        related="order_binding_id.backend_id", store=True, index=True
    )

    external_ref = fields.Char(string="External Reference", index=True)
    external_values = fields.Serialized()

    _unique_binding = models.Constraint(
        "unique(order_binding_id, odoo_id)",
        "This order line is already bound.",
    )

    @api.depends("odoo_id.name")
    def _compute_display_name(self):
        for binding in self:
            binding.display_name = binding.odoo_id.name or "?"
