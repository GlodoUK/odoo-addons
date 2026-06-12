from odoo import models
from odoo.exceptions import AccessError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_invoices(self, grouped=False, final=False, date=None):
        # Preserve the caller's value: the local `grouped` is reused below as an
        # account.move accumulator, shadowing the parameter.
        grouped_param = grouped

        if not self.env["account.move"].has_access("create"):
            try:
                self.check_access("write")
            except AccessError:
                return self.env["account.move"]

        partners_to_group = self.mapped("partner_invoice_id").filtered(
            lambda p: p.sale_invoice_consolidation == "grouped"
        )

        partners_to_split = self.mapped("partner_invoice_id").filtered(
            lambda p: p.sale_invoice_consolidation == "ungrouped"
        )

        grouped_ids = self.filtered(lambda x: x.partner_invoice_id in partners_to_group)
        ungrouped_ids = self.filtered(
            lambda x: x.partner_invoice_id in partners_to_split
        )
        other_ids = self - grouped_ids - ungrouped_ids

        grouped = self.env["account.move"]
        ungrouped = self.env["account.move"]
        others = self.env["account.move"]
        if grouped_ids:
            # Consolidated: merge all of a partner's orders into one invoice.
            # In Odoo grouped=False means "group by partner/shipping/currency".
            grouped = super(SaleOrder, grouped_ids)._create_invoices(
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
        return others + grouped + ungrouped
