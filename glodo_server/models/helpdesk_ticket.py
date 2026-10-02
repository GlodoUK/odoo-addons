from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    glodo_instance_ids = fields.One2many(
        related="partner_id.commercial_partner_id.glodo_instance_ids"
    )

    def action_view_instance(self):
        """View instance for this contact."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Instance - %(name)s", name=self.name),
            "res_model": "glodo.instance",
            "view_mode": "form",
            "domain": [("partner_id.commercial_partner_id", "=", self.id)],
            "res_id": self.glodo_instance_ids[0].id
            if len(self.glodo_instance_ids) == 1
            else False,
        }
