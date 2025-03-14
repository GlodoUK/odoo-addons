from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"
    commercial_partner_id = fields.Many2one(store=True)
    is_private = fields.Boolean(
        string="Private",
        help="Aside from internal staff, only the ticket creator, "
        "listed Customer and anyone added as a follower who is "
        "in the Customers organisation will be able "
        "to see/read the ticket.",
        tracking=True,
    )

    def _privacy_possible_followers(self):
        self.ensure_one()

        return self.env["res.partner"].search(
            [
                ("id", "child_of", self.commercial_partner_id.id),
                ("id", "not in", self.message_partner_ids.ids),
            ]
        )
