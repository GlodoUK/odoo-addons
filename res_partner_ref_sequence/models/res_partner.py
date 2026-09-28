from odoo import models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

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
                raise UserError(
                    self.env._(
                        "No partner reference rule matches %(partner)s.",
                        partner=partner.display_name,
                    )
                )
            partner.ref = rule.sequence_id.next_by_id()
        return True
