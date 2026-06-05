import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

INVOICE_FREQUENCY_DELTAS = {
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
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
        ],
        string="Auto-Invoice Frequency",
        company_dependent=True,
        help="If set, pending sale orders for this customer are automatically "
        "invoiced on this cadence by the scheduled action. Leave empty to "
        "disable automatic invoicing.",
    )

    sale_auto_invoice_next_date = fields.Date(
        string="Next Auto-Invoice Date",
        company_dependent=True,
        help="Date on which the next automatic invoice run is due for this "
        "customer. Orders accumulate until this date is reached, then the "
        "date rolls forward by the configured frequency.",
    )

    def _sale_auto_invoice_advance(self):
        """
        Return this partner's next billing date on a fixed grid.

        Billing dates form a fixed grid: a customer billed monthly on the 1st
        stays on the 1st. We add whole frequency periods to the current
        ``sale_auto_invoice_next_date`` until the result is in the future, so
        the cadence never drifts to whenever the cron happened to run, and any
        missed periods (a delayed or skipped run) are caught up in a single
        jump rather than invoiced one per run. Falls back to today as the
        anchor when no date is set yet.
        """
        self.ensure_one()
        delta = INVOICE_FREQUENCY_DELTAS.get(self.sale_auto_invoice_frequency)
        if not delta:
            return False
        today = fields.Date.context_today(self)
        next_date = (self.sale_auto_invoice_next_date or today) + delta
        while next_date <= today:
            next_date += delta
        return next_date

    @api.model
    def _cron_auto_create_invoices(self):
        """
        Auto-invoice pending sale orders for customers that are due.

        Driven by the set of invoiceable orders rather than by all partners:
        we only look at the (company, invoice partner) pairs that actually have
        something to invoice, then skip those whose schedule is not yet due.

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
        for (company, partner), company_orders in groups.items():
            partner = partner.with_company(company)
            today = fields.Date.context_today(partner)
            next_date = partner.sale_auto_invoice_next_date
            # Due when auto-invoicing is enabled and the date has arrived or passed.
            if (
                not partner.sale_auto_invoice_frequency
                or not next_date
                or next_date > today
            ):
                # Not due (or disabled): count it as handled, commit nothing extra.
                if from_cron and not self.env["ir.cron"]._commit_progress(processed=1):
                    break
                continue
            try:
                # Safe to combine with _commit_progress because
                # the commit happens at the end of the loop body, after the
                # savepoint has already been released - it never spans a
                # _commit_progress call...
                with self.env.cr.savepoint():
                    moves = company_orders.with_company(company)._create_invoices(
                        final=True,
                    )
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
