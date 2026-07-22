from odoo import api, models
from odoo.tools import float_compare


class GateRule(models.Model):
    _inherit = "gate.rule"

    @api.model
    def _selection_trigger(self):
        return super()._selection_trigger() + [
            ("on_confirm", "On sale order confirmation"),
            ("on_edit", "On edit after confirmation"),
        ]

    @api.model
    def _selection_condition(self):
        return super()._selection_condition() + [
            ("over_limit", "Customer over credit limit"),
            ("proforma", "Proforma (pay-now) payment term"),
        ]

    def _condition_over_limit(self, record):
        """Trips when the customer's outstanding balance (plus this order, while still
        unconfirmed) exceeds their credit limit."""
        self.ensure_one()
        partner = record.partner_id.commercial_partner_id
        if not partner.credit_limit:
            return False
        exposure = partner.credit
        if record.state in ("draft", "sent"):
            exposure += record.amount_total
        rounding = (partner.currency_id or record.currency_id).rounding or 0.01
        return (
            float_compare(exposure, partner.credit_limit, precision_rounding=rounding)
            > 0
        )

    def _condition_proforma(self, record):
        """Trips when the payment term is a single 100%-due-immediately line."""
        self.ensure_one()
        term = record.payment_term_id
        if not term or len(term.line_ids) != 1:
            return False
        line = term.line_ids
        return (
            line.value == "percent"
            and float_compare(line.value_amount, 100.0, precision_digits=2) == 0
            and (getattr(line, "nb_days", 0) or 0) == 0
        )
