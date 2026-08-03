from odoo import api, fields, models


class AutolinkTestRecord(models.Model):
    """Minimal mail.thread record that creates a contact for its sender.

    This mirrors what a real application does with incoming mail — see
    'project.task.message_new', "Auto create partner if not existent when the
    task is created from email" — which is the case this module exists for. Most
    applications do not: 'crm.lead.message_new' only reuses an author resolved
    with no_create=True, so it never reaches this module.

    Registered by the gateway test only, never by the module itself.
    """

    _name = "autolink.test.record"
    _description = "Autolink Test Record"
    _inherit = ["mail.thread"]

    name = fields.Char()
    partner_id = fields.Many2one("res.partner", string="Contact")

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        custom_values = dict(custom_values or {})
        if not msg_dict.get("author_id") and msg_dict.get("email_from"):
            author = self.env["mail.thread"]._partner_find_from_emails_single(
                [msg_dict["email_from"]], no_create=False
            )
            msg_dict["author_id"] = author.id
        custom_values.setdefault("partner_id", msg_dict.get("author_id"))
        return super().message_new(msg_dict, custom_values=custom_values)
