from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pricelist_check_warning = fields.Text(
        compute="_compute_pricelist_check_warning",
    )

    @api.depends(
        "state",
        "pricelist_id.check_sale_behaviour",
        "order_line.product_id",
        "order_line.pricelist_item_id",
    )
    def _compute_pricelist_check_warning(self):
        """Warn while the quotation is being built, rather than only when it
        is confirmed, so it is not sent to the customer with lines that will
        never confirm."""
        for order in self:
            invalid = (
                order.state in ("draft", "sent")
                and order._pricelist_check_invalid_lines()
            )
            order.pricelist_check_warning = (
                self.env._(
                    "This quotation cannot be confirmed: the following products"
                    " are not available on the pricelist %(pricelist)s:\n"
                    "%(products)s",
                    pricelist=order.pricelist_id.display_name,
                    products="\n".join(invalid.product_id.mapped("display_name")),
                )
                if invalid
                else False
            )

    def _pricelist_check_invalid_lines(self):
        self.ensure_one()
        return self.order_line.filtered(
            lambda x: x.product_id and not x._pricelist_check_sale_behaviour()
        )

    def _confirmation_error_message(self):
        res = super()._confirmation_error_message()
        if res:
            return res

        invalid = self._pricelist_check_invalid_lines()
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
        if self.env.context.get("skip_sale_check_product_pricelist"):
            return True

        self.ensure_one()
        if not self.product_id:
            return True
        behaviour = self.order_id.pricelist_id.check_sale_behaviour
        method = getattr(self, f"_pricelist_check_sale_behaviour_{behaviour}", None)
        if not method:
            return True
        return method()

    def _pricelist_check_sale_behaviour_explicit(self):
        """A product is on the pricelist when the rule that prices it is.

        A rule computed from another pricelist - a discount or formula with
        base "pricelist", such as a catch-all onto a parent pricelist - only
        passes the product on. When that pricelist is itself explicit, the
        product has to be on it too, so the chain is followed down to the rule
        that actually prices it.
        """
        item = self.pricelist_item_id
        seen = set()
        while (
            item
            and item.compute_price != "fixed"
            and item.base == "pricelist"
            and item.base_pricelist_id.check_sale_behaviour == "explicit"
            # Odoo refuses recursive pricelists; this only guards the loop
            and item.base_pricelist_id.id not in seen
        ):
            seen.add(item.base_pricelist_id.id)
            item = self.env["product.pricelist.item"].browse(
                item.base_pricelist_id._get_product_rule(
                    product=self.product_id,
                    **self._get_pricelist_kwargs(),
                )
            )
        return bool(item)
