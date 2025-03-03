from odoo import models


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def _action_done(self, feedback=False, attachment_ids=None):
        for activity in self.sudo():
            record = (
                self.env[activity.res_model_id.model].sudo().browse(activity.res_id)
            )
            if activity.res_model_id.model == "sale.order":
                record.skip_credit_control_rules = True
        return super()._action_done(feedback, attachment_ids)
