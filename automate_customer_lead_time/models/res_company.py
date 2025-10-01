from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_lead_time_method = fields.Selection(
        [
            ("customer", "Standard Method"),
            ("replace", "Use Vendor Only"),
            ("add", "Customer + Vendor"),
            ("max", "Max Customer v Vendor"),
            ("min", "Min Customer v Vendor"),
        ],
        default="customer",
        required=True,
        string="Default Customer Lead Time Method",
        help="""Method to calculate the customer lead time based on vendor lead time.
        Can be overridden per product.
        - Standard Method: Standard Odoo behaviour. Uses only the customer lead time.
        - Use Vendor Only: Replaces the customer lead time with the vendor lead time.
        - Customer + Vendor: Adds the vendor lead time to the customer lead time.
        - Max Customer v Vendor: Use whichever is greater, customer or vendor lead time.
        - Min Customer v Vendor: Use whichever is least, customer or vendor lead time.
        """,
    )
