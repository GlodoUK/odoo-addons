from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    FORWARDING_WRITEABLE_FIELDS = [
        "forwarding_enabled",
        "forwarding_rule_ids",
    ]

    forwarding_enabled = fields.Boolean(
        related="partner_id.forwarding_enabled", readonly=False
    )
    forwarding_rule_ids = fields.One2many(
        related="partner_id.forwarding_rule_ids", readonly=False
    )

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + self.FORWARDING_WRITEABLE_FIELDS

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + self.FORWARDING_WRITEABLE_FIELDS

    def action_open_forwarding_rules(self):
        self.ensure_one()
        return self.partner_id.action_open_forwarding_rules()
