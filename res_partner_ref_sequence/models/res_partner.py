from odoo import fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    ref_sequence_rule_matched = fields.Boolean(
        compute="_compute_ref_sequence_rule_matched",
    )

    def _compute_ref_sequence_rule_matched(self):
        rules = self.env["res_partner_ref_sequence.rule"]
        for partner in self:
            partner.ref_sequence_rule_matched = bool(rules._resolve(partner))

    def action_generate_ref(self):
        rules = self.env["res_partner_ref_sequence.rule"]
        for partner in self:
            if partner.ref:
                raise UserError(
                    self.env._(
                        "%(partner)s already has the reference %(ref)s.",
                        partner=partner.display_name,
                        ref=partner.ref,
                    )
                )
            rule = rules._resolve(partner)
            if not rule:
                continue
            partner.ref = rule.sequence_id.next_by_id()
        return True
