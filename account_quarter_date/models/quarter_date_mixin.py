from dateutil.relativedelta import relativedelta

from odoo import fields, models


class QuarterDateMixin(models.AbstractModel):
    _name = "quarter.date.mixin"
    _description = "Quarter Date Mixin"

    quarter_date_field = fields.Char(
        string="Quarter Date Field",
        compute="_compute_quarter_date_field",
    )
    fiscal_quarter = fields.Char(
        compute="_compute_fiscal_quarter",
        store=True,
        string="Fiscal Quarter",
        index=True,
    )
    fiscal_year = fields.Integer(
        compute="_compute_fiscal_quarter",
        store=True,
        string="Fiscal Year (Start Year)",
        index=True,
    )

    def _compute_quarter_date_field(self):
        # Abstract method to define the field to use for the quarter date
        # Should be overwritten in the model if the field is not 'create_date'
        for record in self:
            record.quarter_date_field = "create_date"

    def _compute_fiscal_quarter(self):
        # Note: When inheriting this method, make sure to include an @api.depends
        # decorator to trigger it for the same field as quarter_date_field
        # and super() to call this
        for record in self:
            record.fiscal_quarter = False
            record.fiscal_year = False
            if not record.quarter_date_field or not hasattr(
                record, str(record.quarter_date_field)
            ):
                continue

            date = getattr(record, str(record.quarter_date_field))
            if not date:
                continue

            company = False
            if hasattr(record, "company_id"):
                company = record.company_id
            elif hasattr(record, "company"):
                company = record.company

            if not company:
                company = self.env.company

            fiscalyear_last_month = company.fiscalyear_last_month
            fiscalyear_last_day = company.fiscalyear_last_day

            date_year = date.year
            if date.month > int(fiscalyear_last_month):
                date_year = date_year + 1

            # Create a date from the fiscalyear_last_day
            # and fiscalyear_last_month abd today_year
            end_date = date.replace(
                month=int(fiscalyear_last_month),
                day=fiscalyear_last_day,
                year=date_year,
            )
            # subtract one year from date
            start_date = end_date + relativedelta(years=-1, days=1)

            q1 = [start_date + relativedelta(months=+i) for i in range(3)]
            q2 = [start_date + relativedelta(months=+i) for i in range(3, 6)]
            q3 = [start_date + relativedelta(months=+i) for i in range(6, 9)]
            q4 = [start_date + relativedelta(months=+i) for i in range(9, 12)]

            # Check if date falls within the start and end date and set label
            if start_date <= date <= end_date:
                if start_date.year == end_date.year:
                    quarter_year = "{}".format(end_date.year)
                else:
                    quarter_year = "{}/{}".format(start_date.year, end_date.year)
            else:
                if start_date.year == end_date.year:
                    quarter_year = "{}".format(end_date.year)
                else:
                    quarter_year = "{}/{}".format(end_date.year, end_date.year + 1)

            # Check the month when the date falls
            if date.month in [i.month for i in q1]:
                quarter = "{} Q1".format(quarter_year)
            elif date.month in [i.month for i in q2]:
                quarter = "{} Q2".format(quarter_year)
            elif date.month in [i.month for i in q3]:
                quarter = "{} Q3".format(quarter_year)
            elif date.month in [i.month for i in q4]:
                quarter = "{} Q4".format(quarter_year)
            else:
                quarter = False

            record.fiscal_quarter = quarter
            record.fiscal_year = start_date.year
