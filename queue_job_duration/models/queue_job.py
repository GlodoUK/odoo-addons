from odoo import models, fields, api


class QueueJob(models.Model):
    _inherit = "queue.job"

    duration = fields.Float(
        compute="_compute_duration",
        store=True
    )

    @api.multi
    @api.depends('date_done')
    def _compute_duration(self):
        for record in self:
            if not record.date_started or not record.date_done:
                record.duration = None
                continue

            record.duration = (record.date_done - record.date_started).total_seconds()
