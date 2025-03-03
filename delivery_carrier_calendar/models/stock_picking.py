from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.one
    @api.depends("move_lines.date_expected")
    # XXX: This is @api.one to preserve compatibility with upstream
    # pylint: disable=api-one-deprecated
    def _compute_scheduled_date(self):
        scheduled_date = False

        if self.carrier_id.carrier_calendar_id:
            if self.move_type == "direct":
                scheduled_date = min(
                    self.move_lines.mapped("date_expected") or [fields.Datetime.now()]
                )
            else:
                scheduled_date = max(
                    self.move_lines.mapped("date_expected") or [fields.Datetime.now()]
                )

            scheduled_date = self.carrier_id.plan_days(
                scheduled_date, safety_lead_days=0
            )

        if scheduled_date:
            self.scheduled_date = scheduled_date
            return

        return super()._compute_scheduled_date()
