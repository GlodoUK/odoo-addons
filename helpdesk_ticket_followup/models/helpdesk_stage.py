from odoo import api, fields, models


class HelpdeskStage(models.Model):
    _inherit = "helpdesk.stage"
    _sql_constraints = [
        ("id_uniq", "unique (id)", "You can set up stage type for team once"),
    ]

    glo_stage_type = fields.Selection(
        [
            ("in_progress", "In Progress"),
            ("customer_update", "Customer Update"),
            ("closed", "Closed stage"),
        ],
        help="You can set this stage only once for team. In case you assign stage"
        " somewhere else - previous one will be reassigned to empty.",
        string="Stage",
    )
    glo_followup_mail_temp_1st = fields.Many2one(
        comodel_name="mail.template",
        string="First Mail template",
        help="User will receive this first mail template reminder"
        " if he does not reply to our message",
    )
    glo_followup_mail_temp_2nd = fields.Many2one(
        comodel_name="mail.template",
        string="Second Mail template",
        help="User will receive this second mail template reminder"
        " if he does not reply to our message",
    )

    def reassign_glo_stage_type(self):
        self.ensure_one()
        if self.glo_stage_type in ["in_progress", "customer_update", "closed"]:
            stage_ids = (
                self.env["helpdesk.stage"]
                .sudo()
                .search(
                    [
                        ("glo_stage_type", "=", self.glo_stage_type),
                        ("id", "!=", self.id),
                    ]
                )
            )
            if stage_ids:
                for stage_id in stage_ids:
                    for team_id in stage_id.team_ids:
                        if team_id in self.team_ids:
                            stage_id.glo_stage_type = False
                            break

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if vals.get("glo_stage_type", False):
            res.reassign_glo_stage_type()
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get("glo_stage_type") or vals.get("team_ids"):
            for obj in self:
                obj.reassign_glo_stage_type()
        return res
