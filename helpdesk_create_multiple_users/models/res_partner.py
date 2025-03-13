from odoo import _, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    def ensure_is_company(self):
        """Lets user know that partner has no company assigned"""
        for obj in self:
            if not obj.is_company:
                raise UserError(_("This function has to be called only on company!"))

    def add_portal_users_to_company(self):
        """Launches wizard that adds portal users to company"""
        self.ensure_one()
        self.ensure_is_company()
        return {
            "name": _("Add portal users to company"),
            "view_mode": "form",
            "view_id": False,
            "view_type": "form",
            "res_model": "add.users.to.company.wizard",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {"default_parent_id": self.id},
        }
