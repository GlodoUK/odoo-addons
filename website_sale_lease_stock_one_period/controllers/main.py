from odoo import http, fields
from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    @route()
    def cart_update_json(
        self, product_id, line_id=None, add_qty=None, set_qty=None, display=True
    ):
        default_period = False
        if not line_id:
            default_period = True

        res = super().cart_update_json(product_id, line_id, add_qty, set_qty, display)

        order = request.website.sale_get_order(force_create=1)
        lease_period_id = fields.first(
            order
            .mapped('order_line')
            .filtered(
                lambda l: l.is_lease
            )
            .mapped('lease_pricing_id')
        )

        line = order.order_line.filtered(
            lambda l: l.id == res.get('line_id')
        )
        if default_period and lease_period_id and line and line.can_lease_product and not line.is_lease and not line.lease_pricing_id:
            default_line_lease_period = request.env['sale_lease_stock.pricing'].search([
                '&', '&',
                ('product_template_id', '=', line.product_id.product_tmpl_id.id),
                '|',
                ('product_variant_ids', '=', False),
                ('product_variant_ids.id', '=', line.product_id.id),
                '|',
                ('pricelist_id', '=', False),
                ('pricelist_id', '=', order.pricelist_id.id),
                ('duration', '=', lease_period_id.duration),
                ('unit', '=', lease_period_id.unit),
            ], limit=1)

            line.write({
                "lease_pricing_id": default_line_lease_period.id,
                "is_lease": True,
            })
            order._compute_lease_info()

            res['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template("website_sale.cart_lines", {
                'website_sale_order': order,
                'date': fields.Date.today(),
                'suggested_products': order._cart_accessories()
            })
            res['website_sale.short_cart_summary'] = request.env['ir.ui.view']._render_template("website_sale.short_cart_summary", {
                'website_sale_order': order,
            })

        if order.warning_lease:
            # XXX: We're overriding the warning message here because there's no
            # convenient way to override the warning message in the javascript.
            res["warning"] = order.warning_lease

        return res

    def checkout_redirection(self, order):
        res = super().checkout_redirection(order)
        if res:
            return res

        if order and order.warning_lease:
            return http.request.redirect("/shop/cart")
