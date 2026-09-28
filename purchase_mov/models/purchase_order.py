from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools import formatLang


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    force_mov = fields.Boolean(
        "Override MOV",
        tracking=True,
        copy=False,
    )

    def button_confirm(self):
        todo = self.filtered(lambda x: x.state in ("draft", "sent"))
        todo._check_mov()
        return super().button_confirm()

    def _get_mov(self):
        """Return this order's minimum order value, in the order's currency.

        The MOV is recorded against the vendor in their Supplier Currency
        (``property_purchase_currency_id``), falling back to the company
        currency when they have none. Both that field and the MOV itself are
        company dependent, hence the ``with_company``.
        """
        self.ensure_one()

        company = self.company_id or self.env.company
        partner = self.partner_id.with_company(company)
        mov = partner.property_purchase_mov

        if not mov:
            return 0.0

        mov_currency = partner.property_purchase_currency_id or company.currency_id

        if not self.currency_id or mov_currency == self.currency_id:
            return mov

        return mov_currency._convert(
            mov,
            self.currency_id,
            company,
            (self.date_order or fields.Datetime.now()).date(),
        )

    def _check_mov(self):
        for order in self:
            if order.force_mov:
                continue

            currency = order.currency_id or order.company_id.currency_id
            mov = order._get_mov()

            if currency.is_zero(mov):
                continue

            if currency.compare_amounts(order.amount_untaxed, mov) >= 0:
                continue

            raise ValidationError(
                self.env._(
                    "You cannot confirm %(order)s: the minimum order value for"
                    " %(partner)s is %(mov)s, but the order is only for"
                    " %(amount)s.",
                    order=order.display_name,
                    partner=order.partner_id.display_name,
                    mov=formatLang(self.env, mov, currency_obj=currency),
                    amount=formatLang(
                        self.env, order.amount_untaxed, currency_obj=currency
                    ),
                )
            )
