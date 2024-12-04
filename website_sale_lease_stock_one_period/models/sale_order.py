from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    has_lease = fields.Boolean(compute="_compute_lease_info", store=True)
    lease_info = fields.Char(
        compute="_compute_leasing",
        string="Primary Leasing Period",
        store=True,
    )

    @api.depends(
        "order_line",
        "order_line.lease_pricing_id",
        "warning_lease",
        "order_line.is_lease",
    )
    def _compute_lease_info(self):
        for record in self:
            record.has_lease = any([record.is_lease for record in record.order_line])

            if record.warning_lease:
                record.lease_info = record.warning_lease
                continue

            order_line = fields.first(record.website_order_line)
            if order_line.is_lease and order_line.lease_pricing_id:
                record.lease_info = "{} {}".format(
                    order_line.lease_pricing_id.duration,
                    order_line.lease_pricing_id.unit,
                )
                continue

            record.lease_info = _("Purchase")

    warning_lease = fields.Char("Lease Warning", compute="_compute_warning_lease")

    @api.depends("order_line", "order_line.is_lease", "order_line.lease_pricing_id")
    def _compute_warning_lease(self):
        for record in self:
            order_line_ids = record.order_line.filtered(
                lambda p: p.product_id and not p.is_delivery
            )

            is_leased_count = len(set(order_line_ids.mapped("is_lease")))
            is_leased_by_duration_count = len(
                set(
                    order_line_ids.mapped(
                        lambda r: (r.lease_pricing_id.duration, r.lease_pricing_id.unit)
                    )
                )
            )

            clear_warning = True

            if is_leased_count > 1:
                record.warning_lease = _(
                    "You cannot mix and match lease and non-lease products in the same order."
                )
                clear_warning = False

            if is_leased_by_duration_count > 1:
                record.warning_lease = _(
                    "You cannot mix and match lease products with different"
                    " periods in the same order."
                )
                clear_warning = False

            if clear_warning:
                record.warning_lease = False

    @api.depends("order_line", "warning_lease")
    def _cart_can_checkout(self):
        res = super()._cart_can_checkout()

        if self.warning_lease:
            res = False

        return res
