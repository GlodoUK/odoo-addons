from odoo import fields, models
from odoo.tools import float_compare, float_is_zero


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    max_sale_order_value_amount = fields.Monetary()
    max_sale_order_value_mode = fields.Selection(
        [
            ("no", "Any"),
            ("amount_total", "Order Total Amount"),
            ("amount_untaxed", "Order Untaxed Amount"),
        ],
        default="no",
        required=True,
    )

    def _match_max_sale_order_value_amount_total(self, order):
        return order.amount_total

    def _match_max_sale_order_value_amount_untaxed(self, order):
        return order.amount_untaxed

    def _match_max_sale_order_value(self, order):
        if not self.max_sale_order_value_amount or not self.max_sale_order_value_mode:
            return True

        if self.max_sale_order_value_mode == "no":
            return True

        if not order:
            return True

        if float_is_zero(
            self.max_sale_order_value_amount,
            precision_rounding=self.currency_id.rounding,
        ):
            return True

        order_amount_in_currency = order.currency_id._convert(
            getattr(
                self, f"_match_max_sale_order_value_{self.max_sale_order_value_mode}"
            )(order),
            self.currency_id,
            date=order.date_order,
        )

        return (
            float_compare(
                order_amount_in_currency,
                self.max_sale_order_value_amount,
                precision_rounding=self.currency_id.rounding,
            )
            <= 0
        )

    def _match(self, partner, order):
        self.ensure_one()
        return super()._match(partner, order) and self._match_max_sale_order_value(
            order
        )
