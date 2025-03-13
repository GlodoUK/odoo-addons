from odoo import _, fields, models
from odoo.exceptions import UserError


class AddUsersToCompanyWizard(models.TransientModel):
    _name = "add.users.to.company.wizard"
    _description = "Add Users To Company Wizard"

    parent_id = fields.Many2one(
        comodel_name="res.partner", domain=[("is_company", "!=", False)], required=True
    )
    user_info_ids = fields.Many2many(
        comodel_name="add.users.to.company.users",
        string="Add Portal Users",
        required=True,
    )
    welcome_message = fields.Text(
        help="This text is included at the end of the email sent to new portal users."
    )

    def ensure_no_users_with_same_emails(self, create_emails):
        """Makes sure there is no email duplicates on creations or
        in list of contacts"""
        if create_emails:
            if len(create_emails) != len(set(create_emails)):
                raise UserError(_("You can not assign same emails for new users"))
            existing_partners = (
                self.env["res.partner"].sudo().search([("email", "in", create_emails)])
            )
            if existing_partners:
                existing_emails = existing_partners.mapped("email")
                raise UserError(
                    _(
                        "Partners with emails %s have been already created. You can "
                        "edit/delete them and try again or go partner's company -> "
                        "Action -> Grant portal access"
                    )
                    % str(set(existing_emails)).replace("{", "").replace("}", "")
                )

    def post_add_users_to_company(self):
        """Creates contacts, put them into portal wizard, and launches it
        to grant portal access"""
        partner_ids = self.env["res.partner"]
        self.ensure_no_users_with_same_emails(self.mapped("user_info_ids.email"))
        for obj in self:
            parent_id = obj.parent_id
            for user_info_id in obj.user_info_ids:
                partner_id = (
                    self.env["res.partner"]
                    .sudo()
                    .create(
                        {
                            "name": user_info_id.name,
                            "parent_id": parent_id.id,
                            "email": user_info_id.email,
                            "is_company": False,
                            "active": True,
                            "type": "contact",
                        }
                    )
                )
                partner_ids += partner_id
            if partner_ids:
                portal_wiz_id = (
                    self.env["portal.wizard"]
                    .sudo()
                    .create(
                        {
                            "partner_ids": partner_ids.ids,
                            "welcome_message": obj.welcome_message,
                        }
                    )
                )
                for portal_wiz_usr_id in portal_wiz_id.user_ids:
                    portal_wiz_usr_id.action_grant_access()


class AddUsersToCompanyUsers(models.TransientModel):
    _name = "add.users.to.company.users"
    _description = "Add Users To Company Users"

    name = fields.Char(required=True)
    email = fields.Char(help="email of invited person", required=True)
    add_usr_to_cmpny_wiz = fields.Many2many(
        comodel_name="add.users.to.company.wizard", string="Add user to company wizard"
    )
