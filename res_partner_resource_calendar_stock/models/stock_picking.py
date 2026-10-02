from datetime import datetime, time

import pytz

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    show_warning_resource_calendar = fields.Boolean(
        compute="_compute_show_warning_resource_calendar",
        search="_search_show_warning_resource_calendar",
    )

    @api.depends("date_deadline", "partner_id.delivery_resource_calendar_id")
    def _compute_show_warning_resource_calendar(self):
        for picking in self:
            picking.show_warning_resource_calendar = (
                picking._show_warning_resource_calendar()
            )

    def _search_show_warning_resource_calendar(self, operator, value):
        if operator != "in":
            return NotImplemented

        picking_ids = self.search(
            [
                ("date_deadline", "!=", False),
                ("partner_id.delivery_resource_calendar_id", "!=", False),
            ]
        )

        warning_ids = picking_ids.filtered(
            lambda p: p._show_warning_resource_calendar()
        ).ids

        return [("id", "in", warning_ids)]

    def _show_warning_resource_calendar(self):
        self.ensure_one()

        delivery_resource_calendar_id = self.partner_id.delivery_resource_calendar_id

        if not self.date_deadline or not delivery_resource_calendar_id:
            return False

        cal_tz_name = delivery_resource_calendar_id.tz or "UTC"
        tz = pytz.timezone(cal_tz_name)

        date_deadline = fields.Datetime.context_timestamp(
            self.with_context(tz=cal_tz_name), self.date_deadline
        ).date()

        date_start_dt = tz.localize(datetime.combine(date_deadline, time.min))

        date_end_dt = tz.localize(datetime.combine(date_deadline, time.max))

        schedules = self.partner_id._get_resource_calendar_schedule(
            date_start_dt, date_end_dt
        )

        intervals = schedules.get(self.partner_id)

        if intervals and any(
            start < date_end_dt and end > date_start_dt for start, end, _ in intervals
        ):
            return False

        return True
