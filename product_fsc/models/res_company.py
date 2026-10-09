from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    fsc_certificate_code = fields.Char(
        string="FSC Certificate Code",
        help="Chain-of-custody certificate code, e.g. XXX-COC-123456.",
    )
    fsc_license_code = fields.Char(
        string="FSC Licence Code",
        help="FSC trademark licence code, e.g. FSC® C123456.",
    )
    fsc_logo = fields.Image(
        string="FSC Logo",
        help="Upload the FSC logo associated with the company's certification.",
        attachment=True,
    )
