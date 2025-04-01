from odoo import api, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    @api.model
    def recompute_all(self):
        return super(
            HelpdeskTicket, self.with_context(skip_helpdesk_rules=True)
        ).recompute_all()

    @api.model_create_multi
    def create(self, vals_list):
        tickets = super(
            HelpdeskTicket, self.with_context(skip_helpdesk_rules=True)
        ).create(vals_list)

        if not self.env.context.get("skip_helpdesk_rules", False):
            for ticket in tickets:
                ticket._apply_team_rules("on_create")

        return tickets

    def write(self, vals):
        if not self.env.context.get("skip_helpdesk_rules", False):
            for ticket in self:
                ticket.with_context(skip_helpdesk_rules=True).sudo()._apply_team_rules(
                    "on_write"
                )
        return super(HelpdeskTicket, self.with_context(skip_helpdesk_rules=True)).write(
            vals
        )

    def _apply_team_rules(self, event):
        self.ensure_one()

        if not self.team_id:
            return

        rule_ids = self.team_id.rule_ids.filtered(lambda r: r.trigger == event)
        rule_ids.apply(self)
