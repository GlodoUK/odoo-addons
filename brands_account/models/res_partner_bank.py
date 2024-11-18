from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    bank_sort_code = fields.Char(related="bank_id.sort_code", string="Bank Sort Code")
    iban = fields.Char(string="IBAN")
