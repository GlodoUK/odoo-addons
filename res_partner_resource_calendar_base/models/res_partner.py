from collections import defaultdict

from pytz import timezone

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    delivery_resource_calendar_id = fields.Many2one(
        "resource.calendar",
        "Delivery Calendar",
    )

    def _get_resource_calendar_schedule(self, start_period, stop_period):
        partner_ids_by_calendar = defaultdict(lambda: self.env["res.partner"])

        for partner in self:
            if partner.delivery_resource_calendar_id:
                partner_ids_by_calendar[partner.delivery_resource_calendar_id] |= (
                    partner
                )

        schedules = {}

        for calendar_id, partner_ids in partner_ids_by_calendar.items():
            intervals = calendar_id._work_intervals_batch(
                start_period,
                stop_period,
                tz=timezone(calendar_id.tz or "UTC"),
            )[False]

            for partner in partner_ids:
                schedules[partner] = intervals

        return schedules
