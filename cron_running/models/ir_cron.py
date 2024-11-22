from odoo import models, api, fields


class IrCron(models.Model):
    _inherit = "ir.cron"

    running = fields.Boolean(
        string="Currently Running",
        compute="_compute_running",
        store=False,
        readonly=True)

    @api.multi
    def _compute_running(self):
        self.env.cr.execute("""
            select
                id
            from ir_cron
            where
                id not in (select id from ir_cron for update skip locked)
        """)

        running_ids = [r[0] for r in self.env.cr.fetchall()]

        for record in self:
            record.running = (record.id in running_ids)
