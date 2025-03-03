from odoo import _, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def button_draft(self):
        if not self.env.user.has_group(
            "account_move_restrict_reset_to_draft.group_account_move_button_draft"
        ):
            raise UserError(
                _(
                    "You are not allowed to change the state of the account move to"
                    " draft."
                )
            )

        return super().button_draft()
