import urllib.parse

from odoo import fields, models

EDINATION_ACTIONS = [
    ("x12_read", "X12 > JSON"),
    ("x12_write", "JSON > X12"),
    ("edifact_read", "EDIFACT > JSON"),
    ("edifact_write", "JSON > EDIFACT"),
]


class EdiEnvelopeRoute(models.Model):
    _inherit = "edi.envelope.route"

    codec = fields.Selection(selection_add=[("edination", "EDI Nation API")])

    codec_edination_url = fields.Char(
        default="https://api.edination.com/v2/", string="EDI Nation API Base URL"
    )
    codec_edination_apikey = fields.Char(string="EDI Nation API Key")
    codec_edination_open = fields.Selection(
        EDINATION_ACTIONS, default=EDINATION_ACTIONS[0], string="EDI Nation Open Codec",
    )
    codec_edination_enclose = fields.Selection(
        EDINATION_ACTIONS,
        default=EDINATION_ACTIONS[1],
        string="EDI Nation Close Codec",
    )

    def _get_codec_edination_open_url(self):
        self.ensure_one()

        return urllib.parse.urljoin(
            self.codec_edination_url, self.codec_edination_open.replace("_", "/")
        )

    def _get_codec_edination_enclose_url(self):
        self.ensure_one()

        return urllib.parse.urljoin(
            self.codec_edination_url, self.codec_edination_enclose.replace("_", "/")
        )
