import datetime

from odoo import api, fields, models

SECONDS_PER_DAY = 24 * 60 * 60  # 86400
APPROX_DAYS_PER_YEAR = 365.2425
SECONDS_PER_YEAR = APPROX_DAYS_PER_YEAR * SECONDS_PER_DAY


class ResPartner(models.Model):
    _inherit = "res.partner"

    relationship_since = fields.Date()
    relationship_age = fields.Integer(compute="_compute_relationship_age")

    @api.depends("relationship_since")
    def _compute_relationship_age(self):
        for record in self:
            if not record.relationship_since:
                record.relationship_age = False
                continue
            age = (datetime.date.today() - record.relationship_since).total_seconds()

            record.relationship_age = round(age / SECONDS_PER_YEAR, 1)
