from odoo import api, fields, models
from odoo.exceptions import AccessError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_auto_invoice_enabled = fields.Boolean(
        string="Automatic Invoicing",
        compute="_compute_sale_auto_invoice_enabled",
        help="Whether the scheduled action will invoice this order. Mirrors the "
        "Auto-Invoice Frequency of the order's invoice address, read in this "
        "order's company - a frequency is what enables automatic invoicing.",
    )

    @api.depends("company_id", "partner_invoice_id.sale_auto_invoice_frequency")
    def _compute_sale_auto_invoice_enabled(self):
        # Read from the invoice address in the order's company, matching what
        # the cron does: the settings are not inherited from the commercial
        # entity, and they are company_dependent.
        for order in self:
            partner = order.partner_invoice_id.with_company(order.company_id)
            order.sale_auto_invoice_enabled = bool(partner.sale_auto_invoice_frequency)

    def _get_invoice_grouping_keys(self):
        keys = super()._get_invoice_grouping_keys()
        if self.env.context.get("sale_invoice_consolidation"):
            # Consolidated customers get one invoice across all their delivery
            # addresses. Fiscal position stays a key, so taxes are never mixed.
            keys = [key for key in keys if key != "partner_shipping_id"]
        return keys

    def _create_account_invoices(self, invoice_vals_list, final):
        if self.env.context.get("sale_invoice_consolidation"):
            for vals in invoice_vals_list:
                line_ids = [
                    command[1]
                    for line in vals["invoice_line_ids"]
                    for command in line[2].get("sale_line_ids", [])
                ]
                orders = self.env["sale.order.line"].browse(line_ids).order_id
                # A merged invoice would otherwise print the first order's
                # delivery address as if it covered every line. Set in the vals,
                # not afterwards: writing it would recompute the fiscal position.
                if len(orders.partner_shipping_id) > 1:
                    vals["partner_shipping_id"] = vals["partner_id"]
        return super()._create_account_invoices(invoice_vals_list, final)

    def _create_invoices(self, grouped=False, final=False, date=None):
        # Preserve the caller's value: the local `grouped` is reused below as an
        # account.move accumulator, shadowing the parameter.
        grouped_param = grouped

        if not self.env["account.move"].has_access("create"):
            try:
                self.check_access("write")
            except AccessError:
                return self.env["account.move"]

        def preference(order):
            return order.partner_invoice_id.sale_invoice_consolidation

        grouped_ids = self.filtered(lambda o: preference(o) == "grouped")
        grouped_delivery_ids = self.filtered(
            lambda o: preference(o) == "grouped_delivery"
        )
        ungrouped_ids = self.filtered(lambda o: preference(o) == "ungrouped")
        other_ids = self - grouped_ids - grouped_delivery_ids - ungrouped_ids

        grouped = self.env["account.move"]
        grouped_delivery = self.env["account.move"]
        ungrouped = self.env["account.move"]
        others = self.env["account.move"]
        if grouped_ids:
            # Consolidated: merge all of a partner's orders into one invoice.
            # In Odoo grouped=False means "group by _get_invoice_grouping_keys".
            # The context also drops the delivery address from the grouping keys.
            grouped = super(
                SaleOrder, grouped_ids.with_context(sale_invoice_consolidation=True)
            )._create_invoices(grouped=False, final=final, date=date)
        if grouped_delivery_ids:
            # Consolidated per delivery address: Odoo's standard grouping.
            grouped_delivery = super(SaleOrder, grouped_delivery_ids)._create_invoices(
                grouped=False, final=final, date=date
            )
        if ungrouped_ids:
            # Individual: one invoice per sale order (grouped=True groups by SO id).
            ungrouped = super(SaleOrder, ungrouped_ids)._create_invoices(
                grouped=True, final=final, date=date
            )
        if other_ids:
            # Partners with no preference: fall back to the caller's choice.
            others = super(SaleOrder, other_ids)._create_invoices(
                grouped=grouped_param, final=final, date=date
            )
        return others + grouped + grouped_delivery + ungrouped
