from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # This company's own chain-of-custody credentials, printed on FSC claims on
    # outgoing documents (delivery notes, invoices) per FSC-STD-40-004.
    fsc_certificate_code = fields.Char(
        string="FSC Certificate Code",
        help="Chain-of-custody certificate code, e.g. XXX-COC-123456.",
    )
    fsc_license_code = fields.Char(
        string="FSC Licence Code",
        help="FSC trademark licence code, e.g. FSC® C123456.",
    )
