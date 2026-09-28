from odoo import fields, models


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    show_in_search_widget = fields.Boolean(
        string="Show in Category Search Widget",
        default=True,
        help=(
            "When enabled, this category will appear as an option in the "
            "website Category Search snippet dropdowns. Uncheck to hide it "
            "from the widget without removing or unpublishing the category."
        ),
    )
