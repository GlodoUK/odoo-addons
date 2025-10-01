from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_lead_time_method = fields.Selection(
        related="company_id.sale_lead_time_method",
        string="Customer Lead Time Method",
        readonly=False,
        required=True,
        help="""Method to calculate the customer lead time based on vendor lead time.
        Can be overridden per product.
        - Standard Method: Standard Odoo behaviour. Uses only the customer lead time.
        - Use Vendor Only: Replaces the customer lead time with the vendor lead time.
        - Customer + Vendor: Adds the vendor lead time to the customer lead time.
        - Max Customer v Vendor: Use whichever is greater, customer or vendor lead time.
        - Min Customer v Vendor: Use whichever is least, customer or vendor lead time.
        """,
    )
