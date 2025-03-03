from odoo import api, fields, models
from odoo.tools import float_compare, float_round


class SaleOrder(models.Model):
    _inherit = "sale.order"

    credit_control_hold = fields.Many2one("mail.activity")
    skip_credit_control_rules = fields.Boolean(string="Skip Credit Rules", copy=False)

    def action_confirm(self):
        for record in self:
            record._check_credit_control()
        return super(
            SaleOrder, self.with_context(skip_check_credit_control=True)
        ).action_confirm()

    def _action_cancel(self):
        if self.credit_control_hold:
            self.credit_control_hold.unlink()

        return super()._action_cancel()

    def _check_credit_control(self, events=None):
        self.ensure_one()

        if not events:
            events = ["confirm_edit", "confirm"]

        if self.skip_credit_control_rules:
            return

        if self._context.get("website_order_tx", False):
            return

        if self._context.get("skip_check_credit_control", False):
            return

        partner_id = self.partner_id.sudo().commercial_partner_id
        policy_id = partner_id.credit_control_policy_id

        if not policy_id:
            policy_id = (
                self.env["credit.control.policy"]
                .sudo()
                .search([("default", "=", True)], limit=1)
            )

        if policy_id:
            return policy_id.check_rules(events, partner_id, self)

    def write(self, values):
        """
        Maintaining the SOs on credit hold after update if before them was in
        """
        before = {}
        for order in self:
            before[order] = (order.amount_total, len(order.order_line))

        result = super().write(values)

        for order in self.filtered(
            lambda r: r.state in ("sale", "done", "reserved")
            and before[r][0] < r.amount_total
            or len(r.order_line) != before[r][1]
        ):
            # total_increase = order.amount_total - before[order][1]
            order._check_credit_control(events=["confirm_edit", "edit"])

        return result


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    credit_control_amount_to_invoice = fields.Monetary(
        compute="_compute_credit_control_outstanding_amount_to_invoice",
        string="Credit Control Amount to Invoice, exc. Tax",
        store=True,
    )

    @api.depends(
        "state",
        "price_reduce",
        "product_id",
        "product_uom_qty",
        "product_uom",
        "qty_invoiced",
    )
    def _compute_credit_control_outstanding_amount_to_invoice(self):
        for line in self:
            amount_to_invoice = 0.0

            if line.product_id and line.product_uom:
                # We do not use qty_to_invoice because we need to "count" this
                # regardless of whether or not it is actually invoice-able.
                # i.e. if the shipping policy is delivered, then it should still
                # count the outstanding value even before the product is delivered.
                uom_qty_to_consider = line.product_uom_qty - line.qty_invoiced

                if (
                    line.state in ["sale", "done"]
                    and float_compare(
                        uom_qty_to_consider,
                        0.0,
                        precision_rounding=line.product_uom.rounding,
                    )
                    != 0
                ):
                    amount_to_invoice = float_round(
                        line.price_reduce * uom_qty_to_consider,
                        precision_rounding=line.product_uom.rounding,
                    )

            line.credit_control_amount_to_invoice = amount_to_invoice
