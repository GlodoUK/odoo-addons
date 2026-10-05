from datetime import datetime, time

import pytz

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    show_warning_resource_calendar = fields.Boolean(
        compute="_compute_show_warning_resource_calendar",
        search="_search_show_warning_resource_calendar",
    )

    @api.depends("commitment_date", "partner_shipping_id.delivery_resource_calendar_id")
    def _compute_show_warning_resource_calendar(self):
        for order in self:
            order.show_warning_resource_calendar = (
                order._show_warning_resource_calendar()
            )

    def _search_show_warning_resource_calendar(self, operator, value):
        if operator != "in":
            return NotImplemented

        order_ids = self.search(
            [
                ("commitment_date", "!=", False),
                ("partner_shipping_id.delivery_resource_calendar_id", "!=", False),
            ]
        )

        warning_ids = order_ids.filtered(
            lambda o: o._show_warning_resource_calendar()
        ).ids

        return [("id", "in", warning_ids)]

    def _show_warning_resource_calendar(self):
        self.ensure_one()

        delivery_resource_calendar_id = (
            self.partner_shipping_id.delivery_resource_calendar_id
        )

        if not self.commitment_date or not delivery_resource_calendar_id:
            return False

        cal_tz_name = delivery_resource_calendar_id.tz or "UTC"
        tz = pytz.timezone(cal_tz_name)

        commitment_date = fields.Datetime.context_timestamp(
            self.with_context(tz=cal_tz_name), self.commitment_date
        ).date()

        date_start_dt = tz.localize(datetime.combine(commitment_date, time.min))

        date_end_dt = tz.localize(datetime.combine(commitment_date, time.max))

        schedules = self.partner_shipping_id._get_resource_calendar_schedule(
            date_start_dt, date_end_dt
        )

        intervals = schedules.get(self.partner_shipping_id)

        if intervals and any(
            start < date_end_dt and end > date_start_dt for start, end, _ in intervals
        ):
            return False

        return True
