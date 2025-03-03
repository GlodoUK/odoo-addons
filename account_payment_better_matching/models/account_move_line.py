from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    reconcile_override = fields.Monetary(
        default=0.0,
        string="Amount to Allocate",
        help="Amount to include in this reconciliation. Leave blank to reconcile full amount",
        currency_field="currency_id",
    )

    @api.multi
    def _reconcile_lines_partial(self, payment_move, debit_moves, credit_moves, field):
        """ This function loops on the 2 recordsets given as parameter as long as it
            can find a debit and a credit to reconcile together. It returns the recordset of the
            account move lines that were not reconciled during the process.
        """
        (debit_moves + credit_moves).read([field])
        to_create = []
        cash_basis = (
            debit_moves
            and debit_moves[0].account_id.internal_type in ("receivable", "payable")
            or False
        )
        cash_basis_percentage_before_rec = {}
        dc_vals = {}
        credit_moves -= payment_move
        while debit_moves and (credit_moves or payment_move):
            debit_move = debit_moves[0]
            if not credit_moves:
                credit_moves += payment_move
                payment_move = False
            credit_move = credit_moves[0]
            company_currency = debit_move.company_id.currency_id
            # We need those temporary value otherwise the computation might be wrong below
            temp_amount_residual = min(
                debit_move.amount_residual, -credit_move.amount_residual
            )
            temp_amount_residual_currency = min(
                debit_move.amount_residual_currency,
                -credit_move.amount_residual_currency,
            )
            dc_vals[(debit_move.id, credit_move.id)] = (
                debit_move,
                credit_move,
                temp_amount_residual_currency,
            )
            amount_reconcile = min(debit_move[field], -credit_move[field])

            # If a reconcile override amount was provided, use that figure for this line instead
            override_move = False
            if (
                debit_move.reconcile_override
                and debit_move.reconcile_override > 0
                and debit_move.reconcile_override < amount_reconcile
            ):
                override_move = debit_move
            elif (
                credit_move.reconcile_override
                and credit_move.reconcile_override > 0
                and credit_move.reconcile_override < amount_reconcile
            ):
                override_move = credit_move

            if override_move:
                amount_reconcile = override_move.reconcile_override
                temp_amount_residual = override_move.currency_id._convert(
                    override_move.reconcile_override,
                    override_move.company_id.currency_id,
                    override_move.company_id,
                    override_move.date,
                )
                if temp_amount_residual_currency != 0:
                    temp_amount_residual_currency = override_move.reconcile_override
                debit_move.reconcile_override = 0
                credit_move.reconcile_override = 0

            # Remove from recordset the one(s) that will be totally reconciled
            # For optimization purpose, the creation of the partial_reconcile are done at the end,
            # therefore during the process of reconciling several move lines, there are actually no recompute performed by the orm
            # and thus the amount_residual are not recomputed, hence we have to do it manually.
            debit_moves[0].amount_residual -= temp_amount_residual
            debit_moves[0].amount_residual_currency -= temp_amount_residual_currency
            if override_move == debit_move or debit_moves[0].amount_residual == 0:
                debit_moves -= debit_move

            credit_moves[0].amount_residual += temp_amount_residual
            credit_moves[0].amount_residual_currency += temp_amount_residual_currency
            if override_move == credit_move or credit_moves[0].amount_residual == 0:
                credit_moves -= credit_move
            # Check for the currency and amount_currency we can set
            currency = False
            amount_reconcile_currency = 0
            if field == "amount_residual_currency":
                currency = credit_move.currency_id.id
                amount_reconcile_currency = temp_amount_residual_currency
                amount_reconcile = temp_amount_residual
            elif bool(debit_move.currency_id) != bool(credit_move.currency_id):
                # If only one of debit_move or credit_move has a secondary currency, also record the converted amount
                # in that secondary currency in the partial reconciliation. That allows the exchange difference entry
                # to be created, in case it is needed. It also allows to compute the amount residual in foreign currency.
                currency = debit_move.currency_id or credit_move.currency_id
                currency_date = (
                    debit_move.currency_id and credit_move.date or debit_move.date
                )
                amount_reconcile_currency = company_currency._convert(
                    amount_reconcile, currency, debit_move.company_id, currency_date
                )
                currency = currency.id

            if cash_basis:
                tmp_set = debit_move | credit_move
                cash_basis_percentage_before_rec.update(
                    tmp_set._get_matched_percentage()
                )

            to_create.append(
                {
                    "debit_move_id": debit_move.id,
                    "credit_move_id": credit_move.id,
                    "amount": amount_reconcile,
                    "amount_currency": amount_reconcile_currency,
                    "currency_id": currency,
                }
            )

        cash_basis_subjected = []
        part_rec = self.env["account.partial.reconcile"]
        with self.env.norecompute():
            for partial_rec_dict in to_create:
                debit_move, credit_move, amount_residual_currency = dc_vals[
                    partial_rec_dict["debit_move_id"],
                    partial_rec_dict["credit_move_id"],
                ]
                # /!\ NOTE: Exchange rate differences shouldn't create cash basis entries
                # i. e: we don't really receive/give money in a customer/provider fashion
                # Since those are not subjected to cash basis computation we process them first
                if (
                    not amount_residual_currency
                    and debit_move.currency_id
                    and credit_move.currency_id
                ):
                    part_rec.create(partial_rec_dict)
                else:
                    cash_basis_subjected.append(partial_rec_dict)

            for after_rec_dict in cash_basis_subjected:
                new_rec = part_rec.create(after_rec_dict)
                # if the pair belongs to move being reverted, do not create CABA entry
                if cash_basis and not (
                    new_rec.debit_move_id + new_rec.credit_move_id
                ).mapped("move_id").mapped("reverse_entry_id"):
                    new_rec.create_tax_cash_basis_entry(
                        cash_basis_percentage_before_rec
                    )
        self.recompute()

        return debit_moves + credit_moves

    @api.multi
    def auto_reconcile_lines_partial(self, payment_move):
        # Create list of debit and list of credit move ordered by date-currency
        debit_moves = self.filtered(lambda r: r.debit != 0 or r.amount_currency > 0)
        credit_moves = self.filtered(lambda r: r.credit != 0 or r.amount_currency < 0)
        debit_moves = debit_moves.sorted(
            key=lambda a: (a.date_maturity or a.date, a.currency_id)
        )
        credit_moves = credit_moves.sorted(
            key=lambda a: (a.date_maturity or a.date, a.currency_id)
        )
        # Compute on which field reconciliation should be based upon:
        if (
            self[0].account_id.currency_id
            and self[0].account_id.currency_id
            != self[0].account_id.company_id.currency_id
        ):
            field = "amount_residual_currency"
        else:
            field = "amount_residual"
        # if all lines share the same currency, use amount_residual_currency to avoid currency rounding error
        if self[0].currency_id and all(
            [x.amount_currency and x.currency_id == self[0].currency_id for x in self]
        ):
            field = "amount_residual_currency"
        # Reconcile lines
        ret = self._reconcile_lines_partial(
            payment_move, debit_moves, credit_moves, field
        )
        self.write({"reconcile_override": 0})
        return ret

    @api.multi
    def partial_reconcile(
        self, payment_move, writeoff_acc_id=False, writeoff_journal_id=False
    ):
        # Empty self can happen if the user tries to reconcile entries which are already reconciled.
        # The calling method might have filtered out reconciled lines.
        if not self:
            return True

        self._check_reconcile_validity()
        # reconcile everything that can be
        remaining_moves = self.auto_reconcile_lines_partial(payment_move)

        writeoff_to_reconcile = self.env["account.move.line"]
        # if writeoff_acc_id specified, then create write-off move with value the remaining amount from move in self
        if writeoff_acc_id and writeoff_journal_id and remaining_moves:
            all_aml_share_same_currency = all(
                [x.currency_id == self[0].currency_id for x in self]
            )
            writeoff_vals = {
                "account_id": writeoff_acc_id.id,
                "journal_id": writeoff_journal_id.id,
            }
            if not all_aml_share_same_currency:
                writeoff_vals["amount_currency"] = False
            writeoff_to_reconcile = remaining_moves._create_writeoff([writeoff_vals])
            # add writeoff line to reconcile algorithm and finish the reconciliation
            remaining_moves = (
                remaining_moves + writeoff_to_reconcile
            ).auto_reconcile_lines()
        return True
