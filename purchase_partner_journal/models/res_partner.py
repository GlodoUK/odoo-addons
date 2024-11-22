from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    property_purchase_journal_id = fields.Many2one(
        "account.journal",
        string="Supplier Purchase Journal",
        company_dependent=True,
        help="The preferred journal for Supplier Purchases",
    )
