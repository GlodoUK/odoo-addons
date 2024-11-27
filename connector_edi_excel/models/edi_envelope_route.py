from odoo import fields, models


class EdiEnvelopeRoute(models.Model):
    _inherit = "edi.envelope.route"

    codec = fields.Selection(
        selection_add=[("excel_file", "Excel File")], ondelete={"excel_file": "cascade"}
    )
