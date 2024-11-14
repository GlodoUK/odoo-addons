from odoo import _, api, fields, models  # noqa


class CrmLead(models.Model):
    _inherit = "crm.lead"

    brand_id = fields.Many2one(
        "glo.brand", string="Brand", help="Select a brand for this sale"
    )