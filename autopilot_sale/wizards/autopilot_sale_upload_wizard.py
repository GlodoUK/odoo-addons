from odoo import fields, models
from odoo.exceptions import UserError


class AutopilotSaleUploadWizard(models.TransientModel):
    """For a partner who emails their files: no connection needed."""

    _name = "autopilot_sale.upload.wizard"
    _description = "Sale EDI File Upload"

    backend_id = fields.Many2one("autopilot_sale.backend", required=True)
    data = fields.Binary(string="File", required=True)
    filename = fields.Char()

    def action_upload(self):
        self.ensure_one()
        if not self.backend_id.supports_import_order:
            raise UserError(
                self.env._(
                    "Dialect %r does not import orders.", self.backend_id.dialect
                )
            )
        file = self.env["autopilot_sale.order.file"].create(
            {
                "backend_id": self.backend_id.id,
                "source": "upload",
                "filename": self.filename,
                "data": self.data,
            }
        )
        file._enqueue()
        return {
            "type": "ir.actions.act_window",
            "res_model": "autopilot_sale.order.file",
            "res_id": file.id,
            "view_mode": "form",
            "target": "current",
        }
