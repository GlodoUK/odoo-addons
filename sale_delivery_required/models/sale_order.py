from odoo import fields, models
from odoo.exceptions import AccessError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    allow_confirm_without_delivery = fields.Boolean(
        default=False,
        help="If checked, the order can be confirmed without a delivery method.",
    )

    def _has_delivery_bypass_group(self):
        return self.env.user.has_group(
            "sale_delivery_required.group_sale_delivery_required_bypass"
        )

    def write(self, vals):
        if (
            vals.get("allow_confirm_without_delivery")
            and not self._has_delivery_bypass_group()
        ):
            raise AccessError(
                self.env._(
                    "You do not have permission to bypass the delivery requirement."
                )
            )
        return super().write(vals)

    def action_confirm(self):
        for order in self:
            if not order.allow_confirm_without_delivery and (
                not order.carrier_id
                or not any(line.is_delivery for line in order.order_line)
            ):
                raise ValidationError(
                    self.env._(
                        "You must select a delivery method before confirming the order."
                    )
                )
        return super().action_confirm()
