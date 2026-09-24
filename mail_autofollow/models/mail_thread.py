from odoo import api, models

CREATE_TRIGGERS = ("on_create", "on_create_or_write")
WRITE_TRIGGERS = ("on_create_or_write",)


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model_create_multi
    def create(self, vals_list):
        # flag the creation so _message_auto_subscribe below can tell a create
        # from a write, and clear it on the result so a later write on those
        # records is not mistaken for one
        records = super(
            MailThread, self.with_context(mail_autofollow_creating=True)
        ).create(vals_list)
        return records.with_context(mail_autofollow_creating=False)

    def _message_auto_subscribe(self, updated_values, followers_existing_policy="skip"):
        res = super()._message_auto_subscribe(
            updated_values, followers_existing_policy=followers_existing_policy
        )
        triggers = (
            CREATE_TRIGGERS
            if self.env.context.get("mail_autofollow_creating")
            else WRITE_TRIGGERS
        )
        self.env["mail_autofollow.rule"]._apply_all(self, triggers)
        return res
