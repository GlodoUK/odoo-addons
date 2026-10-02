from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class GlodoRemoteUserUnarchiveWizard(models.TransientModel):
    _name = "glodo.remote.user.unarchive.wizard"
    _description = "Temporary Unarchive Remote User"

    _duration_max = models.Constraint(
        "CHECK (duration < 13)",
        "Duration must be less than 13 hours",
    )

    is_reactivate_until = fields.Boolean(
        "Temporary Unarchive",
        default=True,
    )

    remote_user_id = fields.Many2one(
        "glodo.remote.user",
        readonly=True,
        required=True,
    )

    reactivate_until = fields.Datetime(
        compute="_compute_reactivate_until",
        store=True,
    )

    duration = fields.Integer(
        default=1,
    )

    @api.depends("duration", "is_reactivate_until")
    def _compute_reactivate_until(self):
        self.reactivate_until = False

        for wizard in self.filtered(lambda w: w.is_reactivate_until):
            wizard.reactivate_until = fields.Datetime.now() + relativedelta(
                hours=wizard.duration
            )

    def action_confirm(self):
        self.ensure_one()

        self.remote_user_id.reactivate_until = (
            self.reactivate_until if self.is_reactivate_until else False
        )

        return self.remote_user_id.action_unarchive_user()
