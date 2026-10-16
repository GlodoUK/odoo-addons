from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _create_scrap_location(self):
        return super(
            ResCompany,
            self.with_context(default_scrap_location=True),
        )._create_scrap_location()
