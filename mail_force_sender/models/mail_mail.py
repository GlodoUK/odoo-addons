from odoo import models, api


class Base(models.AbstractModel):
    _inherit = 'base'

    def _get_forced_mail_local_part(self, mail_alias):
        self.ensure_one()

        return "%s+%s-%d" % (
            mail_alias,
            self._name,
            self.id
        )


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def create(self, vals):
        records = super(MailMail, self).create(vals)
        if 'email_from' not in vals:
            records._force_email_from()
        return records

    @api.multi
    def _force_email_from(self):
        if self.env.context.get("skip_mail_force_sender", False):
            return

        icp = self.env['ir.config_parameter'].sudo()
        mail_force_sender = icp.get_param('mail.force_sender', False)

        if not mail_force_sender or mail_force_sender == "0":
            return

        mail_from = None

        # default odoo catchall address
        mail_alias = icp.get_param('mail.catchall.alias')
        mail_domain = icp.get_param('mail.catchall.domain')

        # custom send-as address
        forced_mail_from = icp.get_param('mail.force_sender.address')
        if forced_mail_from:
            forced_mail_alias, _force_partition, forced_mail_domain = forced_mail_from.partition('@')  # noqa
            if forced_mail_alias:
                mail_alias = forced_mail_alias
            if forced_mail_domain:
                mail_domain = forced_mail_domain

        if mail_alias and mail_domain:
            mail_from = "%s@%s" % (mail_alias, mail_domain)

        if not mail_domain:
            return

        for mail in self:
            send_as = mail_from

            # Dynamically name the local part, if we want/can
            if mail_force_sender == "2" and self.model and self.res_id:
                local_part = self.env[self.model].browse(self.res_id)._get_forced_mail_local_part(mail_alias)  # noqa

                if local_part:
                    send_as = "%s@%s" % (
                        local_part,
                        mail_domain
                    )

            if send_as:
                mail.with_context(skip_mail_force_sender=True).write({
                    'email_from': send_as
                })
