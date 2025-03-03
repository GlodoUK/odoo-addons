from odoo import models
from odoo.osv import expression


class Website(models.Model):
    _inherit = "website"

    def sale_product_domain(self):
        domain = super(Website, self).sale_product_domain()

        if not self.env.user:
            return domain

        idx = 0

        try:
            idx = domain.index(("sale_ok", "=", True))
        except ValueError:
            return domain

        # Some users may not be able to lease products
        # Some users may not be able to outright purchase products
        # In these scenarios we must hide those items where relevant.

        sale_ok_domain = domain.pop(idx)
        product_domain_components = []

        if self.env.user.sale_ok:
            product_domain_components.append([sale_ok_domain])

        if self.env.user.lease_ok:
            product_domain_components.append([("lease_ok", "=", True)])

        product_domain = expression.OR(product_domain_components)
        domain = expression.AND([product_domain, domain])
        return domain
