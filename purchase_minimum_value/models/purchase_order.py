from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, format_amount


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _should_check_minimum_purchase_value(self):
        self.ensure_one()
        return (
            self.state in ["draft", "sent"]
            and self.partner_id.property_minimum_purchase_order_action == "block"
            and self.partner_id.property_minimum_purchase_order_currency_id
            and self.partner_id.property_minimum_purchase_order_value > 0
        )

    def button_confirm(self):
        for record in self:
            if not record._should_check_minimum_purchase_value():
                continue

            limit_in_purchase_currency = (
                record.partner_id.property_minimum_purchase_order_currency_id._convert(
                    record.partner_id.property_minimum_purchase_order_value,
                    record.currency_id,
                    record.company_id,
                    record.date_order,
                )
            )

            if (
                float_compare(
                    limit_in_purchase_currency,
                    record.amount_untaxed,
                    precision_digits=record.currency_id.rounding,
                )
                > 0
            ):
                raise UserError(
                    _(
                        "Total purchase order value of %(total)s is less than"
                        " the partner's minimum of %(limit)s!"
                    )
                    % {
                        "total": format_amount(
                            self.env, record.amount_untaxed, record.currency_id
                        ),
                        "limit": format_amount(
                            self.env, limit_in_purchase_currency, record.currency_id
                        ),
                    }
                )

        return super().button_confirm()
