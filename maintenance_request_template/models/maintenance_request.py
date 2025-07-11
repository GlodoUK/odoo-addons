from odoo import api, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        for request, vals in zip(self, vals_list):
            if request.equipment_id:
                vals["description"] = request.equipment_id._get_description()
        return vals_list

    @api.onchange("equipment_id")
    def _onchange_equipment_id_template_id(self):
        self.ensure_one()
        if self.equipment_id:
            self.description = self.equipment_id._get_description()
