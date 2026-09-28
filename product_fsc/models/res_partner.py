from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # The FSC certificate belongs to the certificate holder (the supplier), not
    # to each product: one certificate covers many products and is renewed as a
    # unit, so it lives here rather than on product.template.
    fsc_certificate_code = fields.Char(
        string="FSC Certificate Code",
        help="Chain-of-custody certificate code, e.g. XXX-COC-123456.",
    )
    fsc_license_code = fields.Char(
        string="FSC Licence Code",
        help="FSC trademark licence code, e.g. FSC® C123456.",
    )
    fsc_certificate = fields.Binary(
        string="FSC Certificate",
        attachment=True,
        help="The FSC certificate document issued to this partner.",
    )
    fsc_certificate_filename = fields.Char(string="FSC Certificate Filename")
    fsc_certificate_expiry = fields.Date(
        string="FSC Certificate Expiry",
        help="Date the FSC certificate is valid until.",
    )
