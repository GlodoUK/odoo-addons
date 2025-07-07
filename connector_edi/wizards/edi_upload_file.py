import base64
import io

from odoo import fields, models

EDI_UPLOAD_FILE_ROUTE_TYPE_OPTIONS = [
    ("envelope", "EDI Envelope Route"),
    ("message", "EDI Message Route"),
]


class EdiUploadFile(models.TransientModel):
    _name = "edi.upload.file"
    _description = "EDI Upload File"

    backend_id = fields.Many2one(
        "edi.backend",
        "EDI Backend",
        required=True,
    )

    envelope_route_id = fields.Many2one(
        "edi.envelope.route",
        "EDI Envelope Route",
    )

    message_route_id = fields.Many2one(
        "edi.route",
        "EDI Message Route",
    )

    file = fields.Binary(
        required=True,
    )

    route_type = fields.Selection(
        EDI_UPLOAD_FILE_ROUTE_TYPE_OPTIONS,
        default="envelope",
        required=True,
    )

    def action_upload(self):
        self.ensure_one()

        route_field = (
            "route_id" if self.route_type == "envelope" else "message_route_id"
        )

        route_id = (
            self.envelope_route_id
            if self.route_type == "envelope"
            else self.message_route_id
        )

        body = base64.b64decode(io.StringIO(self.file.decode("utf-8")).read()).decode(
            "utf-8"
        )

        res = self.env[f"edi.{self.route_type}"].create(
            {
                "body": body,
                "direction": "in",
                "backend_id": self.backend_id.id,
                "external_id": "File Upload",
                "partner_id": self.backend_id.partner_id.id,
                route_field: route_id.id,
            }
        )

        res.action_pending()
