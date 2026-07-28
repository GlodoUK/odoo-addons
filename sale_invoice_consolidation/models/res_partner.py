import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

INVOICE_FREQUENCY_DELTAS = {
    "hourly": relativedelta(hours=1),
    "daily": relativedelta(days=1),
    "weekly": relativedelta(weeks=1),
    "monthly": relativedelta(months=1),
    "quarterly": relativedelta(months=3),
}


class ResPartner(models.Model):
    _inherit = "res.partner"

    sale_invoice_consolidation = fields.Selection(
        [
            ("grouped", "Consolidated"),
            ("ungrouped", "Individual"),
        ],
        company_dependent=True,
        string="Invoice Consolidation Preference",
    )

    sale_auto_invoice_frequency = fields.Selection(
        [
            ("hourly", "Hourly"),
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
        ],
        string="Auto-Invoice Frequency",
        company_dependent=True,
        help="If set, pending sale orders for this customer are automatically "
        "invoiced on this cadence by the scheduled action. Leave empty to "
        "disable automatic invoicing. Sub-day cadences (hourly) only take "
        "effect if the scheduled action itself runs at least that often.",
    )

    sale_auto_invoice_next_date = fields.Datetime(
        string="Next Auto-Invoice Run",
        company_dependent=True,
        help="Date and time at which the next automatic invoice run is due for "
        "this customer. Orders accumulate until this moment is reached, then it "
        "rolls forward by the configured frequency. Stored and compared in UTC.",
    )

    def _sale_auto_invoice_advance(self):
        """
        Return this partner's next billing moment on a fixed grid.

        Billing moments form a fixed grid: a customer billed monthly on the 1st
        stays on the 1st, an hourly customer stays on the same minute past the
        hour. We add whole frequency periods to the current
        ``sale_auto_invoice_next_date`` until the result is in the future, so
        the cadence never drifts to whenever the cron happened to run, and any
        missed periods (a delayed or skipped run) are caught up in a single
        jump rather than invoiced one per run. Falls back to now as the anchor
        when no value is set yet. Works in UTC, like the stored field.
        """
        self.ensure_one()
        delta = INVOICE_FREQUENCY_DELTAS.get(self.sale_auto_invoice_frequency)
        if not delta:
            return False
        now = fields.Datetime.now()
        next_date = (self.sale_auto_invoice_next_date or now) + delta
        while next_date <= now:
            next_date += delta
        return next_date

    @api.model
    def _cron_auto_create_invoices(self):
        """
        Auto-invoice pending sale orders for customers that are due.

        Driven by the set of invoiceable orders rather than by all partners:
        we only look at the (company, invoice partner) pairs that actually have
        something to invoice, then skip those whose schedule is not yet due.

        Whether credit notes may be raised by the run is controlled per company
        by ``res.company.sale_auto_invoice_credit_notes``.

        Progress is reported through ``ir.cron._commit_progress`` so each pair
        is committed as it completes: a timed-out run resumes where it left off
        instead of redoing everything, and a failure rolls back only the pair
        being processed.
        """
        from_cron = bool(self.env.context.get("cron_id"))
        orders = self.env["sale.order"].search(
            [
                ("state", "=", "sale"),
                ("invoice_status", "=", "to invoice"),
            ]
        )
        groups = orders.grouped(lambda o: (o.company_id, o.partner_invoice_id))
        if from_cron:
            self.env["ir.cron"]._commit_progress(remaining=len(groups))
        now = fields.Datetime.now()
        for (company, partner), company_orders in groups.items():
            partner = partner.with_company(company)
            next_date = partner.sale_auto_invoice_next_date
            # Due when auto-invoicing is enabled and the moment has arrived or passed.
            if (
                not partner.sale_auto_invoice_frequency
                or not next_date
                or next_date > now
            ):
                # Not due (or disabled): count it as handled, commit nothing extra.
                if from_cron and not self.env["ir.cron"]._commit_progress(processed=1):
                    break
                continue
            # `final` is what makes Odoo invoice negative pending quantities and
            # switch the resulting negative moves to credit notes, so the company
            # setting is exactly the "raise credit notes automatically" switch.
            final = company.sale_auto_invoice_credit_notes
            company_orders = company_orders.with_company(company)
            if not final:
                # Without `final`, negative quantities are not invoiceable: an
                # order left with nothing else would make _create_invoices raise
                # "nothing to invoice" and stall this customer's schedule
                # forever. Drop those orders and let them wait for a manual
                # credit note.
                company_orders = company_orders.filtered(
                    lambda o: any(
                        not line.display_type
                        for line in o._get_invoiceable_lines(final=False)
                    )
                )
            try:
                # Safe to combine with _commit_progress because
                # the commit happens at the end of the loop body, after the
                # savepoint has already been released - it never spans a
                # _commit_progress call...
                with self.env.cr.savepoint():
                    moves = self.env["account.move"]
                    if company_orders:
                        moves = company_orders._create_invoices(final=final)
                    partner.sale_auto_invoice_next_date = (
                        partner._sale_auto_invoice_advance()
                    )
                    if moves:
                        partner._message_log(
                            body=self.env._(
                                "%(count)s invoice(s) automatically raised for "
                                "%(orders)s pending sale order(s).",
                                count=len(moves),
                                orders=len(company_orders),
                            )
                        )
            except Exception:
                _logger.exception(
                    "Scheduled invoicing failed for partner %s (id=%s) "
                    "in company %s (id=%s)",
                    partner.display_name,
                    partner.id,
                    company.display_name,
                    company.id,
                )

            if from_cron and not self.env["ir.cron"]._commit_progress(processed=1):
                break
