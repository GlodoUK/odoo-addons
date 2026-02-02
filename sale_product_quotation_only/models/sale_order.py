from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        quotation_only_line_ids = self.order_line.filtered(
            lambda x: x.product_id.quotation_only
        )

        if quotation_only_line_ids:
            error_msg = [
                f"{line.order_id.name}: {line.product_id.name}"
                for line in quotation_only_line_ids
            ]

            raise UserError(
                _(
                    "Products marked as Quotation Only cannot be added to a "
                    "confirmed sale order.\n%s"
                )
                % "\n".join(error_msg)
            )

        return super().action_confirm()
