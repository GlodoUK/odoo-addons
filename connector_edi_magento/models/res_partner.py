from odoo import fields, models


class EdiResParter(models.Model):
    _inherit = "edi.res.partner"

    magento_customer_is_guest = fields.Boolean(default=False)


class ResPartner(models.Model):
    _inherit = "res.partner"

    edi_magento_address_ids = fields.One2many("edi.magento.address", "odoo_id")
