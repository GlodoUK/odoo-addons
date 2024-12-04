from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def website_sale_ok(self):
        self.ensure_one()

        return self.env.user.commercial_partner_id.sale_ok and self.sale_ok

    def website_lease_ok(self):
        self.ensure_one()

        return self.env.user.commercial_partner_id.lease_ok and self.lease_ok

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1,
        pricelist=False,
        parent_combination=False,
        only_template=False,
    ):
        combination_info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            pricelist=pricelist,
            parent_combination=parent_combination,
            only_template=only_template,
        )

        if combination_info.get("product_id"):
            product = self.env["product.product"].browse(
                combination_info.get("product_id")
            )
        else:
            product = self.env["product.product"].search(
                [("product_tmpl_id", "=", combination_info.get("product_template_id"))],
                limit=1,
            )

        if product:
            combination_info.update(
                {
                    "lease_ok": self.lease_ok,
                }
            )

        if product and product.website_lease_ok():
            combination_info.update(
                {
                    "lease_pricing_rules": {
                        rule.id: {
                            "name": rule.display_name,
                            "price": rule.price,
                            "unit": rule.unit,
                            "duration": rule.duration,
                            "unit_l10n": dict(
                                rule._fields["unit"]._description_selection(self.env)
                            ).get(rule.unit),
                        }
                        for rule in product._get_lease_price_rules(pricelist=pricelist)
                    }
                }
            )

        return combination_info


class ProductProduct(models.Model):
    _inherit = "product.product"

    def website_sale_ok(self):
        self.ensure_one()

        return self.product_tmpl_id.website_sale_ok()

    def website_lease_ok(self):
        self.ensure_one()

        return self.product_tmpl_id.website_lease_ok()
