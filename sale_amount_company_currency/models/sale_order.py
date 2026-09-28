from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    company_currency_id = fields.Many2one(
        string="Company Currency",
        related="company_id.currency_id",
    )

    amount_untaxed_company = fields.Monetary(
        "Untaxed Amount (Company Currency)",
        compute="_compute_amount_company",
        currency_field="company_currency_id",
        store=True,
    )

    amount_tax_company = fields.Monetary(
        "Taxes (Company Currency)",
        compute="_compute_amount_company",
        currency_field="company_currency_id",
        store=True,
    )

    amount_total_company = fields.Monetary(
        "Total (Company Currency)",
        compute="_compute_amount_company",
        currency_field="company_currency_id",
        store=True,
    )

    @api.depends(
        "company_id",
        "currency_id",
        "date_order",
        "amount_untaxed",
        "amount_tax",
        "amount_total",
    )
    def _compute_amount_company(self):
        for order in self:
            order.amount_untaxed_company = order.currency_id._convert(
                order.amount_untaxed,
                order.company_id.currency_id,
                order.company_id,
                (order.date_order or fields.Datetime.now()).date(),
            )

            order.amount_tax_company = order.currency_id._convert(
                order.amount_tax,
                order.company_id.currency_id,
                order.company_id,
                (order.date_order or fields.Datetime.now()).date(),
            )

            order.amount_total_company = order.currency_id._convert(
                order.amount_total,
                order.company_id.currency_id,
                order.company_id,
                (order.date_order or fields.Datetime.now()).date(),
            )
