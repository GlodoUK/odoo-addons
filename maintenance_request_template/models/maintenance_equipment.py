from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    template_id = fields.Many2one(
        "maintenance.equipment.template",
    )

    def _get_template_id(self):
        if not self:
            return self
        self.ensure_one()
        return self.template_id or self.category_id.template_id
