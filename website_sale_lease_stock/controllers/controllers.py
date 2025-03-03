import json

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.variant import VariantController


class WebsiteSaleVariantController(VariantController):
    @http.route()
    def get_combination_info_website(
        self, product_template_id, product_id, combination, add_qty, **kw
    ):
        res = super().get_combination_info_website(
            product_template_id, product_id, combination, add_qty, **kw
        )

        try:
            lease = int(kw.get("leasing", 0))
        except (ValueError, TypeError):
            lease = 0

        if lease and lease in res.get("lease_pricing_rules", {}).keys():
            rule = res.get("lease_pricing_rules", {}).get(lease, {})

            res.update(
                {
                    "price": rule.get("price"),
                    "list_price": rule.get("price"),
                }
            )

        return res


class WebsiteSaleController(WebsiteSale):
    @http.route(
        ["/shop/cart/update"],
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != "draft":
            request.session["sale_order_id"] = None
            sale_order = request.website.sale_get_order(force_create=True)

        product_custom_attribute_values = None
        if kw.get("product_custom_attribute_values"):
            product_custom_attribute_values = json.loads(
                kw.get("product_custom_attribute_values")
            )

        no_variant_attribute_values = None
        if kw.get("no_variant_attribute_values"):
            no_variant_attribute_values = json.loads(
                kw.get("no_variant_attribute_values")
            )

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            lease=kw.get("lease"),
        )

        if kw.get("express"):
            return request.redirect("/shop/checkout?express=1")

        return request.redirect("/shop/cart")
