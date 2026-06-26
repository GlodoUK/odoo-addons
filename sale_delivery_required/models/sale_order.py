from odoo import fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    allow_confirm_without_delivery = fields.Boolean(
        default=False,
        help="If checked, the order can be confirmed without a delivery method.",
    )

    def action_confirm(self):
        has_bypass = self.env.user.has_group(
            "sale_delivery_required.group_sale_delivery_required_bypass"
        )
        for order in self:
            if (
                not has_bypass
                and not order.allow_confirm_without_delivery
                and (
                    not order.carrier_id
                    or not any(line.is_delivery for line in order.order_line)
                )
            ):
                raise ValidationError(
                    self.env._(
                        "You must select a delivery method before confirming the order."
                    )
                )
        return super().action_confirm()
