import base64
import io

from odoo import fields, models


class EdiUploadFile(models.TransientModel):
    _name = "edi.upload.file"
    _description = "Upload File to EDI"

    backend_id = fields.Many2one("edi.backend", string="EDI Backend", required=True)
    file = fields.Binary(required=True)
    route_type = fields.Selection(
        [
            ("envelope", "Envelope Route"),
            ("message", "Message Route"),
        ],
        default="envelope",
        required=True,
    )
    envelope_route_id = fields.Many2one("edi.envelope.route")
    message_route_id = fields.Many2one("edi.route")

    def action_upload(self):
        self.ensure_one()
        route_field = (
            "route_id" if self.route_type == "envelope" else "message_route_id"
        )
        route = (
            self.envelope_route_id
            if self.route_type == "envelope"
            else self.message_route_id
        )
        body = base64.b64decode(io.StringIO(self.file.decode("utf-8")).read()).decode(
            "utf-8"
        )
        res = self.env["edi.%s" % self.route_type].create(
            {
                "backend_id": self.backend_id.id,
                "partner_id": self.backend_id.partner_id.id,
                "external_id": "File Upload",
                route_field: route.id,
                "body": body,
                "direction": "in",
            }
        )
        res.action_pending()
