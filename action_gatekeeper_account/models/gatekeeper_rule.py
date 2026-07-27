from odoo import fields, models


class GatekeeperRule(models.Model):
    _inherit = "gatekeeper.rule"

    target_model = fields.Selection(
        selection_add=[
            ("account.move", "Invoice/Journal Entry"),
        ],
        ondelete={"account.move": "cascade"},
    )
    target_move_type = fields.Selection(
        [
            ("out_invoice", "Customer Invoice"),
            ("in_invoice", "Vendor Bill"),
            ("out_refund", "Customer Credit Note"),
            ("in_refund", "Vendor Credit Note"),
            ("entry", "Journal Entry"),
            ("all_customer", "All Customer Invoices/Credit Notes"),
            ("all_vendor", "All Vendor Bills/Credit Notes"),
            ("all", "All"),
        ],
    )
