from odoo import api, models


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _force_sender(self, vals):
        IrConfig = self.env["ir.config_parameter"].sudo()

        mail_force_sender = IrConfig.get_param("mail.force_sender")

        if not mail_force_sender:
            return vals

        # custom send-as address
        mail_force_sender_address = IrConfig.get_param(
            "mail.force_sender.address"
        )  # noqa

        # default odoo catchall address
        mail_alias = IrConfig.get_param("mail.catchall.alias")
        mail_domain = IrConfig.get_param("mail.catchall.domain")

        if mail_force_sender_address:
            vals["email_from"] = mail_force_sender
        elif mail_alias and mail_domain:
            mail_part = mail_alias

            vals["email_from"] = "%s@%s" % (mail_part, mail_domain)

        return vals

    @api.model
    def create(self, vals):
        vals = self._force_sender(vals)
        return super(MailMail, self).create(vals)

    def write(self, vals):
        vals = self._force_sender(vals)
        return super(MailMail, self).write(vals)
