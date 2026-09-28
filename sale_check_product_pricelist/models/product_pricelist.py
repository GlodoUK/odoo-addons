from odoo import fields, models


class ProductPriceList(models.Model):
    _inherit = "product.pricelist"

    check_sale_behaviour = fields.Selection(
        selection=[
            ("default", "Odoo default - fallback to MSRP"),
            ("explicit", "Only those on Pricelist"),
        ],
        string="Sellable Products",
        default="default",
        required=True,
        help="Odoo default: any product can be sold, falling back to its sales"
        " price when no rule on this pricelist matches.\n"
        "Only those on Pricelist: confirming an order is blocked unless"
        " every line matches a rule on this pricelist.",
    )
