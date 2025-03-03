from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    reconcile_override = fields.Monetary(
        default=0.0,
        string="Amount to Allocate",
        help="Amount to include in this reconciliation. Leave blank to reconcile full"
        " amount",
        currency_field="company_currency_id",
    )

    def _prepare_reconciliation_partials(self):
        if not self._context.get("partial_reconcile", False):
            return super()._prepare_reconciliation_partials()
        partial_values = []
        payment_line = self._context.get("payment_move_line")
        for line in self:
            if line == payment_line:
                continue
            if line.reconciled:
                continue
            override_amount = line.reconcile_override
            if override_amount == 0:
                continue
            line_currency_amount = override_amount
            if line.currency_id and line.currency_id != line.company_currency_id:
                line_currency_amount = line.company_currency_id._convert(
                    override_amount,
                    line.currency_id,
                    line.company_id,
                    line.date,
                )
            payment_currency_amount = override_amount
            if (
                payment_line.currency_id
                and payment_line.currency_id != payment_line.company_currency_id
            ):
                payment_currency_amount = payment_line.currency_id._convert(
                    override_amount,
                    payment_line.company_id.currency_id,
                    payment_line.company_id,
                    payment_line.date,
                )
            if payment_line.debit > 0:
                debit_line = payment_line
                credit_line = line
                debit_amount = payment_currency_amount
                credit_amount = line_currency_amount
            else:
                debit_line = line
                credit_line = payment_line
                debit_amount = line_currency_amount
                credit_amount = payment_currency_amount

            partial_values.append(
                {
                    "debit_move_id": debit_line.id,
                    "credit_move_id": credit_line.id,
                    "amount": line.reconcile_override,
                    "debit_amount_currency": debit_amount,
                    "credit_amount_currency": credit_amount,
                }
            )
        return partial_values
