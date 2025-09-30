from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sale_delay_method = fields.Selection(
        [
            ("add", "Customer + Vendor"),
            ("replace", "Use Vendor Only"),
            ("max", "Max Customer v Vendor"),
            ("min", "Min Customer v Vendor"),
        ],
        default="add",
        required=True,
        string="Customer Lead Time Method",
        help="""Method to calculate the customer lead time based on vendor lead time.
        - Customer + Vendor: Adds the vendor lead time to the customer lead time.
        - Use Vendor Only: Replaces the customer lead time with the vendor lead time.
        - Max Customer v Vendor: Use whichever is greater, customer or vendor lead time.
        - Min Customer v Vendor: Use whichever is least, customer or vendor lead time.
        """,
    )
