from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    glodo_instance_ids = fields.One2many(
        related="partner_id.commercial_partner_id.glodo_instance_ids"
    )

    def action_view_instance(self):
        """View instances for this ticket's customer."""
        self.ensure_one()

        return self.partner_id.commercial_partner_id.action_view_instance()
