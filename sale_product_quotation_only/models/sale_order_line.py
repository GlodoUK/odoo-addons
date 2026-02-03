from odoo import _, api, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def _check_quotation_only_product_allowed_states(self):
        return ["draft", "sent", "cancel"]

    # ruff: noqa: E501
    @api.constrains("product_id")
    def _check_quotation_only_product(self):
        quotation_only_line_ids = self.filtered(
            lambda x: x.product_id.quotation_only
            and x.order_id.state
            not in self._check_quotation_only_product_allowed_states()
        )

        if quotation_only_line_ids:
            error_msg = [
                f"{line.order_id.name}: {line.product_id.name}"
                for line in quotation_only_line_ids
            ]

            raise ValidationError(
                _(
                    "Products marked as Quotation Only cannot be added to a "
                    "confirmed sale order.\n%s"
                )
                % "\n".join(error_msg)
            )
