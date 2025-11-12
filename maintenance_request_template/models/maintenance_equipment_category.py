from odoo import fields, models


class MaintenanceEquipmentCategory(models.Model):
    _inherit = "maintenance.equipment.category"

    template_id = fields.Many2one(
        "maintenance.equipment.template",
    )
