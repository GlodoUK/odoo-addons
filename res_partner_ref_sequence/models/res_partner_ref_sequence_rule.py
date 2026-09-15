from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain
from odoo.tools.safe_eval import safe_eval


class ResPartnerRefSequenceRule(models.Model):
    _name = "res_partner_ref_sequence.rule"
    _description = "Partner Reference Rule"
    _order = "sequence, id"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10, string="Priority")
    domain = fields.Char(
        required=True,
        default="[]",
        help="Partners matching this domain get their reference from this "
        "rule's sequence. An empty domain matches every partner.",
    )
    sequence_id = fields.Many2one(
        "ir.sequence",
        required=True,
        ondelete="restrict",
        help="References of matching partners are drawn from this sequence.",
    )

    @api.constrains("domain")
    def _check_domain(self):
        for rule in self:
            try:
                Domain(rule._get_domain()).validate(self.env["res.partner"])
            except Exception as error:
                raise ValidationError(
                    self.env._(
                        "%(rule)s has an invalid domain: %(error)s",
                        rule=rule.display_name,
                        error=error,
                    )
                ) from error

    def _get_domain(self):
        self.ensure_one()
        return safe_eval(self.domain or "[]")

    @api.model
    def _resolve(self, partner):
        partner.ensure_one()
        for rule in self.search([]):  # pylint: disable=no-search-all
            if partner.filtered_domain(rule._get_domain()):
                return rule
        return self.browse()
