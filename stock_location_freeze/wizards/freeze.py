from odoo import _, api, fields, models


class StockLocationFreeze(models.TransientModel):
    _name = "stock.location.freeze"
    _description = "Freeze Stock Location"

    location_id = fields.Many2one("stock.location", required=True)
    freeze_reason_id = fields.Many2one("stock.location.freeze.reason", required=True)
    warning_message = fields.Text(compute="_compute_warning_message")

    @api.depends("location_id")
    def _compute_warning_message(self):
        for wizard in self:
            if not wizard.location_id:
                wizard.warning_message = False
                continue

            reserved_quants = self.env["stock.quant"].search_count(
                [
                    ("location_id", "child_of", wizard.location_id.id),
                    ("reserved_quantity", ">", 0),
                ]
            )

            if reserved_quants > 0:
                wizard.warning_message = _(
                    "Warning: There is reserved stock in this location "
                    "(or its sub-locations). Freezing this location will prevent "
                    "these items from being picked or unreserved until the freeze "
                    "is removed."
                )
            else:
                wizard.warning_message = False

    def action_freeze(self):
        self.ensure_one()
        if self.location_id.frozen:
            return {"type": "ir.actions.act_window_close"}

        self.location_id.write(
            {
                "frozen": True,
                "freeze_reason_id": self.freeze_reason_id.id,
                "freeze_uid": self.env.uid,
                "freeze_date": fields.Datetime.now(),
                "unfreeze_uid": False,
                "unfreeze_date": False,
            }
        )
        return {"type": "ir.actions.act_window_close"}
