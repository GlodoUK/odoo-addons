import human_readable

from odoo import _, api, fields, models


class CrmLeadStageChangeTracker(models.Model):
    _name = "crm.lead.stage.change.tracker"
    _description = "CRM Lead Stage Change Tracker"

    crm_lead_id = fields.Many2one(comodel_name="crm.lead", ondelete="cascade")
    crm_stage_id = fields.Many2one(comodel_name="crm.stage")
    crm_stage_name = fields.Char(related="crm_stage_id.name", store=True)

    @api.model
    def get_stage_duration(self, crm_lead):
        """
        Fetches the last stage change of the crm.lead registered and compute
        the time delta between that and the present time
        """
        track = self.search(
            [("crm_lead_id", "=", crm_lead.id)], order="id desc", limit=1
        )
        duration = None
        if track:
            duration = human_readable.date_time(
                fields.Datetime.now() - track.create_date
            ).replace(" ago", "")

        return duration

    @api.model
    def monitor_n_log_stage_duration(self, crm_lead):
        """
        Monitor and log onto the chatter the duration a lead/opportunity spent at
        the last stage transitioned from
        """
        crm_lead.ensure_one()
        self.create(
            {
                "crm_lead_id": crm_lead.id,
                "crm_stage_id": crm_lead.stage_id.id,
            }
        )
        tracks = self.search(
            [
                ("crm_lead_id", "=", crm_lead.id),
            ],
            limit=2,
            order="id desc",
        )

        if len(tracks) == 2:
            cur_track, prev_track = tracks
            duration = abs(cur_track.create_date - prev_track.create_date)
            duration = human_readable.date_time(duration).replace(" ago", "")
            message = _(
                "Lead/Opportunity was at stage %(stage)s for %(duration)s",
                stage=prev_track.crm_stage_name,
                duration=duration,
            )
            crm_lead.message_post(body=_(message))
