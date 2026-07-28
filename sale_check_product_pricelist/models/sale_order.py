from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _confirmation_error_message(self):
        res = super()._confirmation_error_message()
        if res:
            return res

        invalid = self.order_line.filtered(
            lambda x: x.product_id and not x._pricelist_check_sale_behaviour()
        )
        if invalid:
            return self.env._(
                "The following lines are not available on the pricelist"
                " %(pricelist)s: %(products)s",
                pricelist=self.pricelist_id.display_name,
                products=", ".join(invalid.product_id.mapped("display_name")),
            )

        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _pricelist_check_sale_behaviour(self) -> bool:
        """
        Return True is sale is OK
        """
        self.ensure_one()
        if not self.product_id:
            return True
        behaviour = self.order_id.pricelist_id.check_sale_behaviour
        method = getattr(self, f"_pricelist_check_sale_behaviour_{behaviour}", None)
        if not method:
            return True
        return method()

    def _pricelist_check_sale_behaviour_explicit(self):
        return bool(self.pricelist_item_id)
