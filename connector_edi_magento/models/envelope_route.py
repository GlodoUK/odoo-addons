from odoo import fields, models


class EnvelopeRoute(models.Model):
    _inherit = "edi.envelope.route"

    is_magento = fields.Boolean(related="backend_id.is_magento", store=True)

    protocol = fields.Selection(
        selection_add=[("magento", "Magento REST API")], ondelete={"magento": "cascade"}
    )

    magento_endpoint = fields.Selection(
        [
            ("products/", "Products"),
            ("orders/", "Orders"),
        ]
    )

    magento_override_existing_products = fields.Boolean(
        string="Override Existing Products", default=False
    )

    magento_filters = fields.Text(
        string="API Filters",
        help="Filters to apply to the Magento REST API call.",
    )

    magento_in_ignore_attributes = fields.Char(
        string="Ignore Attributes",
        help="Attributes to ignore when importing from Magento. (comma separated)",
    )
    magento_in_readonly_attributes = fields.Char(
        string="Readonly Attributes",
        help="Attributes to mark as readonly when exporting to Magento. (comma"
        " separated)",
    )
    magento_skip_cancelled_orders = fields.Boolean(
        string="Skip Cancelled Orders",
        help="Skip cancelled orders when importing from Magento.",
    )
    magento_skip_unpaid_orders = fields.Boolean(
        string="Skip Unpaid Orders",
        help="Skip unpaid orders when importing from Magento.",
    )

    codec = fields.Selection(
        selection_add=[("magento", "Magento")],
        ondelete={"magento": "cascade"},
    )
