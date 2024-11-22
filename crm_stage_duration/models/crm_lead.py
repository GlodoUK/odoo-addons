from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    stage_change_track_ids = fields.One2many(
        comodel_name="crm.lead.stage.change.tracker", inverse_name="crm_lead_id"
    )
    stage_duration = fields.Char(compute="_compute_stage_duration")

    @api.depends("stage_change_track_ids")
    def _compute_stage_duration(self):
        for lead in self:
            lead.stage_duration = self.env[
                "crm.lead.stage.change.tracker"
            ].get_stage_duration(lead)

    def write(self, vals):
        res = super().write(vals)
        if "stage_id" in vals:
            for lead in self:
                self.env["crm.lead.stage.change.tracker"].monitor_n_log_stage_duration(
                    lead
                )
        return res

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        for lead in leads:
            self.env["crm.lead.stage.change.tracker"].monitor_n_log_stage_duration(lead)
        return leads
