from lxml.builder import E

from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _get_default_leaflet_view(self):
        view = E.leaflet()

        return view
