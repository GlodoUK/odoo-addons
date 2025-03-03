from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _commercial_fields(self):
        return super(ResPartner, self)._commercial_fields() + [
            "credit_control_policy_id",
        ]

    credit_control_limit = fields.Monetary()
    credit_control_used = fields.Monetary(
        compute="_compute_credit_control_used",
        readonly=True,
    )
    credit_control_policy_id = fields.Many2one(
        "credit.control.policy",
        required=False,
        index=True,
    )

    def _compute_credit_control_used(self):
        commercial_partner_ids = (
            self.mapped("commercial_partner_id")
            .filtered(lambda p: p.credit_control_policy_id)
            .ids
        )

        due_all = {}

        if commercial_partner_ids:
            tables, where_clause, where_params = (
                self.env["account.move.line"]
                .with_context(company_id=self.env.company.id)
                ._query_get()
            )
            where_params = [tuple(commercial_partner_ids)] + where_params
            if where_clause:
                where_clause = "AND " + where_clause

            # pylint: disable=sql-injection
            self._cr.execute(
                """
                SELECT
                    account_move_line__move_id.commercial_partner_id,
                    SUM(case
                        when act.type = 'receivable' then
                            account_move_line.amount_residual
                        else
                            account_move_line.amount_residual * -1
                    end)
                FROM {tables}
                INNER JOIN account_move AS account_move_line__move_id ON
                    (account_move_line__move_id.id=account_move_line.move_id)
                LEFT JOIN account_account a ON
                    (account_move_line.account_id=a.id)
                LEFT JOIN account_account_type act ON
                    (a.user_type_id=act.id)
                WHERE
                    act.type IN (
                        'receivable',
                        'payable'
                    )
                    AND account_move_line__move_id.commercial_partner_id IN %s
                    AND account_move_line.reconciled IS NOT TRUE
                    {where_clause}
                GROUP BY
                    account_move_line__move_id.commercial_partner_id
                """.format(
                    tables=tables,
                    where_clause=where_clause,
                ),
                where_params,
            )

            due_all = {pid: val for pid, val in self._cr.fetchall()}

        for partner in self:
            if not partner.commercial_partner_id.credit_control_policy_id:
                partner.credit_control_used = 0.0
                continue

            # Collect all confirmed, but not yet invoiced sale order lines
            sale_order_line_ids = self.env["sale.order.line"].search(
                [
                    (
                        "order_partner_id.commercial_partner_id",
                        "=",
                        partner.commercial_partner_id.id,
                    ),
                    ("state", "in", ["sale", "done"]),
                    ("invoice_status", "!=", "invoiced"),
                ]
            )
            confirmed_so_not_invoiced = 0.0
            for order_line in sale_order_line_ids:
                if not order_line.is_downpayment:
                    confirmed_so_not_invoiced += order_line.currency_id._convert(
                        order_line.credit_control_amount_to_invoice,
                        partner.currency_id,
                        order_line.company_id,
                        order_line.order_id.date_order,
                    )

                if order_line.is_downpayment and order_line.qty_invoiced != 0:
                    confirmed_so_not_invoiced -= order_line.currency_id._convert(
                        order_line.price_total,
                        partner.currency_id,
                        order_line.company_id,
                        order_line.order_id.date_order,
                    )

            partner.credit_control_used = (
                due_all.get(partner.commercial_partner_id.id, 0.0)
                + confirmed_so_not_invoiced
            )
