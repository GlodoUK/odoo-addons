from odoo import api, fields, models
from odoo.exceptions import ValidationError


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
    released_user_ids = fields.Many2many(
        comodel_name="res.users", readonly=True, string="Released By"
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
    release_count_required = fields.Integer(
        related="rule_id.release_count_required", store=True, string="Required Releases"
    )
    release_count = fields.Integer(
        compute="_compute_release_count",
    )
    user_has_released = fields.Boolean(
        compute="_compute_release_count",
    )

    @api.depends("released_user_ids", "rule_id.release_count_required")
    def _compute_release_count(self):
        for line in self:
            line.release_count = len(line.released_user_ids)
            line.user_has_released = self.env.user in line.released_user_ids

    def _compute_can_release(self):
        for line in self:
            line.can_release = (
                self.env.user in line.rule_id.release_users
                or self.env.user in line.rule_id.release_groups.mapped("user_ids")
            ) and not line.user_has_released

    def action_release(self):
        for line in self:
            line.rule_id._check_can_release(self.env.user)
            line.released_user_ids = [(4, self.env.user.id)]
            if line.release_count >= line.rule_id.release_count_required:
                line.is_released = True
                line.released_on = fields.Datetime.now()
            record = self.env[line.res_model].browse(line.res_id)
            if all(line.is_released for line in record.gatekeeper_rule_lines):
                record._release_gatekeeper_hold()

    def action_request_release(self):
        for line in self:
            release_partners = line.rule_id.release_users.mapped("partner_id")
            release_partners |= line.rule_id.release_groups.mapped(
                "user_ids.partner_id"
            )
            release_partners -= line.released_user_ids.mapped("partner_id")
            release_partners -= self.env.user.partner_id
            if not release_partners:
                raise ValidationError(
                    self.env._(
                        "No users available to request release from for this rule."
                    )
                )
            record = self.env[line.res_model].browse(line.res_id)
            record.message_post(
                body=self.env._(
                    "Release requested for Gatekeeper Rule: %s", line.rule_name
                ),
                message_type="notification",
                subtype_xmlid="mail.mt_comment",
                partner_ids=release_partners.ids,
            )
