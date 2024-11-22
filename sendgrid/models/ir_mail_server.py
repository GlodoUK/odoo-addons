import re
from email.utils import formataddr, parseaddr

from odoo import api, fields, models, tools


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    from_method = fields.Selection(
        [
            ("default", "Odoo Default"),
            ("catchall", "Catchall"),
            ("msg_id", "Message ID"),
            ("on_behalf", "On-Behalf Of"),
            ("odoo_object", "Odoo Object"),
        ],
        "From/Reply-To Method",
        default="default",
        required=True,
    )

    @api.model
    def send_email(
        self, message, mail_server_id=None, smtp_server=None, *args, **kwargs
    ):
        from_method = "default"

        # Find the mail server we're using, or default to the config

        if mail_server_id:
            mail_server = self.sudo().browse(mail_server_id)
            from_method = mail_server.from_method
        elif not smtp_server:
            mail_server = self.sudo().search([], order="sequence", limit=1)
            from_method = mail_server.from_method

        if not from_method:
            from_method = tools.config.get("smtp_from_method", "default")

        icp = self.env["ir.config_parameter"].sudo()
        # default odoo catchall address
        mail_alias = icp.get_param("mail.catchall.alias")
        mail_domain = icp.get_param("mail.catchall.domain")
        email_from = None

        if from_method == "default" or not mail_alias or not mail_domain:
            return super(IrMailServer, self).send_email(
                message, mail_server_id, smtp_server, *args, **kwargs
            )

        original_email_from = parseaddr(message.get("From"))

        if from_method in ["msg_id", "odoo_object"] and message.get(
            "Message-Id"
        ):  # noqa
            # The message_id isn't unique. Prefer the one that has a
            # model set and only pick the first record. Odoo does
            # almost the same thing in mail.thread.message_route().
            msg = (
                self.sudo()
                .env["mail.message"]
                .search(
                    [("message_id", "=", message.get("Message-Id"))],
                    order="model",
                    limit=1,
                )
            )
            if msg and from_method == "msg_id":
                email_from = "%s+%d@%s" % (mail_alias, msg.id, mail_domain)
            elif (
                msg
                and from_method == "odoo_object"
                and msg.model
                and msg.res_id  # noqa
            ):
                email_from = "%s+%d@%s" % (msg.model, msg.res_id, mail_domain)
            else:
                from_method = "catchall"

        if from_method == "on_behalf":
            if not original_email_from[1]:
                # if there is no sender, we default to catchall
                from_method = "catchall"
            elif original_email_from[1].split("@")[1] != mail_domain:
                # if the original senders domain matches, then we do nothing,
                # otherwise we replace the local part and do "mailgun" style
                # "on-behalf of"
                email_from = "%s@%s" % (
                    re.sub(
                        r"[^A-Za-z0-9!#$%&'+\-/=?^_`{\|}~]",
                        "=",
                        original_email_from[1],  # noqa
                    ),
                    mail_domain,
                )
                email_from = email_from

        if from_method == "catchall":
            email_from = "%s@%s" % (mail_alias, mail_domain)

        if email_from:
            message.replace_header(
                "From", formataddr((original_email_from[0], email_from))
            )

            bounce_alias = icp.get_param("mail.bounce.alias")
            if not bounce_alias:
                # then, bounce handling is disabled and we want
                # Return-Path = From
                if "Return-Path" in message:
                    message.replace_header("Return-Path", email_from)
                else:
                    message.add_header("Return-Path", email_from)

        return super(IrMailServer, self).send_email(
            message, mail_server_id, smtp_server, *args, **kwargs
        )
