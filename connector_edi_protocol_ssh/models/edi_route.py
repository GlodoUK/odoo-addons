from odoo import fields, models

PROTOCOL_PORT_DICT = {
    "ftps": 990,
}


class EdiEnvelopeRoute(models.Model):
    _inherit = "edi.envelope.route"

    protocol = fields.Selection(
        selection_add=[
            ("sftp", "SFTP (SSH File Transfer Protocol)"),
            ("scp", "SCP (SSH Secure File Copy)"),
        ],
        ondelete={
            "sftp": "cascade",
            "scp": "cascade",
        },
    )

    ssh_host = fields.Char()
    ssh_port = fields.Integer(default=22)
    ssh_username = fields.Char()
    ssh_password = fields.Char()
    ssh_path_in = fields.Char()
    ssh_path_out = fields.Char()
    ssh_delete = fields.Boolean()
