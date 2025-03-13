from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    ticket_followup_ids = fields.One2many(
        comodel_name="helpdesk.ticket.followup",
        inverse_name="helpdesk_ticket_id",
    )

    def return_stage_by_type(self, stage_type):
        """Takes glo_stage_type string, returns stage_id connected
        to same helpdesk team"""
        self.ensure_one()
        stage_id = (
            self.env["helpdesk.stage"]
            .sudo()
            .search(
                [
                    ("glo_stage_type", "=", stage_type),
                    ("team_ids", "in", self.team_id.id),
                ]
            )
        )
        if not stage_id:
            raise UserError(
                _(
                    "Please, set up In Progress stage in glo_stage_type"
                    " field for %s helpdesk team. "
                )
                % self.team_id.name
            )
        return stage_id

    def return_sibling_users(self, partner_id):
        """Returns registered users from same company"""
        user_sibling_ids = self.env["res.users"]
        if partner_id.parent_id:
            for child_partner_id in partner_id.parent_id.child_ids:
                if child_partner_id.user_ids:
                    if child_partner_id.user_ids[0] not in user_sibling_ids:
                        user_sibling_ids += child_partner_id.user_ids[0]
            return user_sibling_ids
        return (
            [self.partner_id.user_ids[0]]
            if self.partner_id.user_ids
            else user_sibling_ids
        )

    def update_ticket_stage(self, author_user_id):
        """Updates stages to:
        - in_progress if our user or his sibling sent message
        - customer_update if our technical_user_id sent message"""
        self.ensure_one()
        stage_type_id = self.env["helpdesk.stage"]
        if author_user_id == self.user_id:
            stage_type_id = self.return_stage_by_type("customer_update")
        partner_user_id = self.return_sibling_users(self.partner_id)
        if partner_user_id and author_user_id in partner_user_id:
            stage_type_id = self.return_stage_by_type("in_progress")
        if stage_type_id and self.stage_id != stage_type_id:
            self.stage_id = stage_type_id.id
        return self

    def update_ticket_followup(self):
        """Updates date on model on customer update refresh,
        removes followups if we are not on customer update stage"""
        for obj in self:
            if obj.stage_id.glo_stage_type == "customer_update":
                if obj.ticket_followup_ids:
                    obj.ticket_followup_ids.reset_ticket_followup()
                else:
                    self.env["helpdesk.ticket.followup"].sudo().create(
                        {
                            "helpdesk_ticket_id": obj.id,
                        }
                    )
            else:
                if obj.ticket_followup_ids:
                    obj.ticket_followup_ids.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if vals_list[0].get("stage_id"):
            res.update_ticket_followup()
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get("stage_id"):
            self.update_ticket_followup()
        return res

    # def return_client_partner_followups(self):
    #     """ Returns customer and all following up clients. """
    #     self.ensure_one()
    #     # Customer
    #     ticket_partner_id = self.partner_id
    #     ticket_partner_sibling_ids = ticket_partner_id.mapped("parent_id.child_ids")
    #     ticket_followup_ids = self.allowed_users.filtered(
    #         lambda partner: partner in ticket_partner_sibling_ids if
    #         ticket_partner_sibling_ids else partner == ticket_partner_id)
    #     return ticket_followup_ids
