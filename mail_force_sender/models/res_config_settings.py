from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    force_mail = fields.Selection([
        ("0", 'Default'),
        ("1", 'Fixed Address'),
        ("2", 'Dynamic Address')
    ])

    force_mail_sender = fields.Char(
        string="Force Email From"
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        icp = self.env['ir.config_parameter'].sudo()

        res.update(
            {
                "force_mail": icp.get_param('mail.force_sender'),
                "force_mail_sender": icp.get_param('mail.force_sender.address'),
            }
        )

        return res

    @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()

        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("mail.force_sender", self.force_mail or "0")
        icp.set_param("mail.force_sender.address", self.force_mail_sender or False)

        return res
