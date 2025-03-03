from odoo import api, fields, models

SEQUENCE_MAPPING_DICT = {
    "all": 2,
    "include": 1,
    "exclude": 0,
}


class ResPartnerForwardingRule(models.Model):
    _name = "res.partner.forwarding.rule"
    _description = "Contact Forwarding Rule"
    _order = "sequence asc"

    sequence = fields.Integer(compute="_compute_sequence", store=True, index=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    mode = fields.Selection(
        [
            ("all", "Any Model"),
            ("include", "Including Model"),
            ("exclude", "Excluding Model"),
        ],
        required=True,
        default="all",
    )
    model_id = fields.Many2one("ir.model", domain="[('is_mail_thread', '=', True)]")
    model_name = fields.Char(related="model_id.model", store=True)
    forwarding_to_partner_id = fields.Many2one(
        "res.partner", required=False, string="Forward To"
    )

    @api.depends("mode")
    def _compute_sequence(self):
        for record in self:
            record.sequence = SEQUENCE_MAPPING_DICT.get(record.mode, 2)

    def _match_rule(self, model_name):
        matching_rule_id = self.env["res.partner.forwarding.rule"]

        for rule_id in self:
            if rule_id.mode == "exclude" and rule_id.model_name == model_name:
                break

            if rule_id.mode == "all" or (
                rule_id.mode == "include" and rule_id.model_name == model_name
            ):
                matching_rule_id = rule_id
                break

        return matching_rule_id

    _sql_constraints = [
        (
            "partner_mode_model_unique",
            "unique (partner_id, mode, model_id)",
            "Mode and Model must be unique per partner",
        )
    ]
