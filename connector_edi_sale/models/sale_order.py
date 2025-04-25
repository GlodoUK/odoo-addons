from odoo import api, fields, models
from odoo.osv import expression


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "edi.message.mixin"]

    edi_sale_order_ids = fields.One2many(
        "edi.sale.order",
        "odoo_id",
        copy=False,
        string="EDI Sale Orders",
    )

    edi_sale_order_count = fields.Integer(
        compute="_compute_edi_sale_order_count",
        store=True,
    )

    @api.depends("edi_sale_order_ids")
    def _compute_edi_sale_order_count(self):
        for order in self:
            order.edi_sale_order_count = len(order.edi_sale_order_ids)

    def _edi_message_ids_domain(self):
        extra_domain = [
            ("model", "=", "edi.sale.order"),
            ("res_id", "in", self.edi_sale_order_ids.ids),
        ]

        return expression.OR(
            [
                super()._edi_message_ids_domain(),
                extra_domain,
            ]
        )
