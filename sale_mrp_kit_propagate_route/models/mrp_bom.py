from odoo import fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    sale_kit_propagate_route = fields.Boolean(
        string="On Sale Components Follow Kit Route",
        default=True,
        help="Restores the behaviour of Odoo 12.0 and earlier, where the kit's "
        "route decided where its components ship from. When this kit is sold "
        "on a sale order, every component ships by the kit's routes (or, if the "
        "kit has none, the warehouse's delivery route) instead of its own, so "
        "the whole kit leaves from one place. Routes chosen on the sale order "
        "line still apply as they are. Since 13.0, core routes each component "
        "by its own routes, and a kit can ship from several places.",
    )
