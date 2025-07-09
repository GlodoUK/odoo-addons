from odoo import api, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    @api.model_create_multi
    def create(self, vals_list):
        maintenance_requests = super().create(vals_list)
        for request in maintenance_requests:
            if request.equipment_id:
                request.description = request.equipment_id._get_description()
        return maintenance_requests

    @api.onchange("equipment_id")
    def _onchange_equipment_id_template_id(self):
        self.ensure_one()
        if self.equipment_id:
            self.description = self.equipment_id._get_description()
