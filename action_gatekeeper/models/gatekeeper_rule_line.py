from odoo import fields, models


class GatekeeperRuleLine(models.Model):
    _name = "gatekeeper.line"
    _description = "Gatekeeper Rule Line"

    rule_id = fields.Many2one(
        comodel_name="gatekeeper.rule",
        required=True,
        ondelete="cascade",
        index=True,
    )
    rule_name = fields.Char(
        related="rule_id.name",
        store=True,
    )
    action = fields.Selection(
        related="rule_id.action",
        store=True,
    )
    trigger = fields.Many2one(
        related="rule_id.trigger",
        store=True,
    )
    is_released = fields.Boolean(
        default=False,
        readonly=True,
    )
    released_by = fields.Many2one(
        comodel_name="res.users",
        readonly=True,
    )
    released_on = fields.Datetime(
        readonly=True,
    )
    can_release = fields.Boolean(
        compute="_compute_can_release",
    )
    res_model = fields.Selection(
        related="rule_id.target_model",
        store=True,
    )
    res_id = fields.Integer(
        string="Resource ID",
    )

    def _compute_can_release(self):
        for line in self:
            line.can_release = (
                self.env.user in line.rule_id.release_users
                or self.env.user in line.rule_id.release_groups.mapped("user_ids")
            )

    def action_release(self):
        for line in self:
            line.rule_id._check_can_release(self.env.user)
            line.is_released = True
            line.released_by = self.env.user
            line.released_on = fields.Datetime.now()
            record = self.env[line.res_model].browse(line.res_id)
            if all(line.is_released for line in record.gatekeeper_rule_lines):
                record._release_gatekeeper_hold()
