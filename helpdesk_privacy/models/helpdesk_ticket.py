from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    is_private = fields.Boolean(
        string="Private",
        help="Aside from internal staff, only the ticket creator, "
        "listed Customer and anyone added as a follower who is "
        "in the Customers organisation will be able "
        "to see/read the ticket.",
    )
    allowed_portal_partner_ids = fields.Many2many(
        "res.partner",
        compute="_compute_allowed_portal_partner_ids",
        string="Allowed Portal Partners",
    )

    def _compute_allowed_portal_partner_ids(self):
        for record in self:
            allowed = self.env["res.partner"]
            if record.is_private:
                allowed |= record.partner_id
            else:
                allowed |= record.mapped("partner_id.parent_id.child_ids")
            record.allowed_portal_partner_ids = allowed
