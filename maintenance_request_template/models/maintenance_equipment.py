from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    template_id = fields.Many2one(
        "maintenance.equipment.template",
    )

    def _get_description(self):
        self.ensure_one()
        return self._get_template_id().description or self.note

    def _get_template_id(self):
        self.ensure_one()
        return self.template_id or self.category_id.template_id
