from urllib.parse import ParseResult, quote, urlunparse

from odoo import _, api, fields, models
from odoo.exceptions import UserError

PROTOCOL_PORT_DICT = {
    "ftps": 990,
}


class EdiEnvelopeRoute(models.Model):
    _inherit = "edi.envelope.route"

    protocol = fields.Selection(
        selection_add=[("ftp", "FTP")], ondelete={"ftp": "cascade"}
    )

    ftp_protocol = fields.Selection(
        [
            ("ftp", "FTP"),
            ("ftpes", "FTP (Explicit)"),
            ("ftps", "FTP (Implicit)"),
        ],
        default="ftp",
        required=True,
    )
    ftp_host = fields.Char()
    ftp_port = fields.Integer(default=21)
    ftp_username = fields.Char()
    ftp_password = fields.Char()
    ftp_path_in = fields.Char()
    ftp_path_out = fields.Char()
    ftp_delete = fields.Boolean()
    ftp_list_method = fields.Selection(
        [
            ("mlsd", "MLSD"),
            ("list", "List"),
        ],
        required=True,
        default="mlsd",
    )

    @api.onchange("ftp_protocol")
    def _onchange_ftp_protocol(self):
        self.ftp_port = PROTOCOL_PORT_DICT.get(self.ftp_protocol, 21)

    def _get_ftp_url(self):
        self.ensure_one()
        if self.protocol != "ftp":
            raise UserError(_("This method is only available for FTP routes."))

        url = {
            "scheme": self.ftp_protocol if not self.ftp_protocol == "ftpes" else "ftp",
            "netloc": (
                "%s:%s@%s:%d"
                % (
                    quote(self.ftp_username),
                    quote(self.ftp_password),
                    self.ftp_host,
                    self.ftp_port,
                )
            ),
            "path": "/",
            "params": "",
            "query": "",
            "fragment": "",
        }

        return urlunparse(ParseResult(**url))

    def _get_ftp_use_ssl(self):
        self.ensure_one()
        if self.protocol != "ftp":
            raise UserError(_("This method is only available for FTP routes."))
        return self.ftp_protocol in ("ftpes", "ftps")
