import csv
from odoo import _, api, fields, models


class EdiEnvelopeRoute(models.Model):
    _inherit = "edi.envelope.route"

    codec = fields.Selection(selection_add=[("csv", "CSV Field")])
    codec_csv_quoting = fields.Selection([
        (csv.QUOTE_MINIMAL, 'Minimal'),
        (csv.QUOTE_ALL, 'All'),
        (csv.QUOTE_NONNUMERIC, 'Non-Numeric Only'),
        (csv.QUOTE_NONE, 'None'),
    ], default=csv.QUOTE_MINIMAL)
    codec_csv_delimiter = fields.Char(default=',')
    codec_csv_field = fields.Integer(string="Field Index", default=0)
