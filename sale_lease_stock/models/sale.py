from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import format_date


class SaleOrder(models.Model):
    _inherit = "sale.order"

    lease_schedule_count = fields.Integer(compute="_compute_lease_schedule_count")

    @api.depends("order_line.lease_schedule_ids")
    def _compute_lease_schedule_count(self):
        for record in self:
            record.lease_schedule_count = len(
                record.mapped("order_line.lease_schedule_ids")
            )

    def action_view_lease_schedules(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "sale_lease_stock.action_window_lease_schedule"
        )
        action["domain"] = [("order_id", "in", self.ids)]
        return action

    def update_prices(self):
        super().update_prices()
        # Apply correct lease prices with respect to pricelist
        for line_id in self.order_line.filtered(lambda line: line.is_lease):
            if not line_id.lease_pricing_id:
                line_id.price_unit = line_id.product_id.lst_price
                continue

            pricing = line_id.lease_pricing_id
            price = pricing.price

            if pricing.currency_id != self.currency_id:
                price = pricing.currency_id._convert(
                    from_amount=price,
                    to_currency=self.currency_id,
                    company=self.company_id,
                    date=fields.Date.today(),
                )
            line_id.price_unit = price

    def action_confirm(self):
        for record in self:
            partner_id = record.partner_id
            lines = record.order_line.filtered(
                lambda line: line.product_id and not line.is_delivery
            )

            if not partner_id.sale_ok and False in lines.mapped("is_lease"):
                raise UserError(
                    _(
                        "You cannot confirm a sale order with a customer that is not "
                        "allowed to sell."
                    )
                )

            if not partner_id.lease_ok and True in lines.mapped("is_lease"):
                raise UserError(
                    _(
                        "You cannot confirm a sale order with a customer that is not "
                        "allowed to lease."
                    )
                )

            if lines.filtered(
                lambda line: line.is_lease and not line.product_id.lease_ok
            ):
                raise UserError(
                    _(
                        "You cannot confirm a sale order with a product that is not "
                        "allowed to be leased."
                    )
                )

            if lines.filtered(
                lambda line: not line.is_lease and not line.product_id.sale_ok
            ):
                raise UserError(
                    _(
                        "You cannot confirm a sale order with a product that is not "
                        "allowed to be sold."
                    )
                )

        res = super().action_confirm()

        for line_id in self.mapped("order_line").filtered(lambda line: line.is_lease):
            duration = line_id.lease_pricing_id.duration

            for i in range(0, duration):
                when = fields.Date.today() + relativedelta(
                    **{line_id.lease_pricing_id.unit: i}
                )

                self.env["sale_lease_stock.lease.schedule"].create(
                    {
                        "line_id": line_id.id,
                        "price": line_id.price_unit,
                        "quantity_to_invoice": line_id.product_uom_qty,
                        "currency_id": line_id.currency_id.id,
                        "state": "pending",
                        "date": when,
                    }
                )

        return res

    def _action_cancel(self):
        res = super()._action_cancel()

        lease_schedule_ids = self.mapped("order_line.lease_schedule_ids")

        if any(
            i in ["done"]
            for i in lease_schedule_ids.mapped("account_move_line_ids.move_id.state")
        ):
            raise UserError(
                _("Cannot cancel an in progress lease with completed invoices")
            )

        move_ids = lease_schedule_ids.mapped("account_move_line_ids.move_id").filtered(
            lambda m: m.state == "draft"
        )
        if move_ids:
            move_ids.button_cancel()

        lease_schedule_ids.unlink()

        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    can_lease_product = fields.Boolean(compute="_compute_can_lease_product")
    is_lease = fields.Boolean(default=False)
    lease_pricing_id = fields.Many2one(
        "sale_lease_stock.pricing",
        index=True,
    )
    date_lease_start = fields.Date(
        default=lambda self: fields.Date.today(),
    )
    date_lease_end = fields.Date(
        compute="_compute_lease_end",
        store=True,
    )
    lease_schedule_ids = fields.One2many("sale_lease_stock.lease.schedule", "line_id")

    @api.onchange("can_lease_product", "order_partner_id")
    def _onchange_can_lease_product(self):
        company_domain = [
            "|",
            ("company_id", "=", False),
            ("company_id", "=", self.company_id),
        ]

        product_domain = []
        partner_id = self.order_partner_id

        if not partner_id:
            product_domain.append(("sale_ok", "=", True))

        if partner_id and partner_id.lease_ok:
            product_domain.append(("lease_ok", "=", True))

        if partner_id and partner_id.sale_ok:
            product_domain = expression.OR(
                [
                    product_domain,
                    [("sale_ok", "=", True)],
                ]
            )

        return {
            "domain": {"product_id": expression.AND([company_domain, product_domain])}
        }

    @api.depends("product_id", "order_partner_id")
    def _compute_can_lease_product(self):
        for record in self:
            if not record.product_id.lease_ok:
                record.can_lease_product = False
                continue

            if not record.order_partner_id.lease_ok:
                record.can_lease_product = False
                continue

            record.can_lease_product = True

    @api.depends(
        "is_lease", "qty_invoiced", "qty_delivered", "product_uom_qty", "order_id.state"
    )
    def _get_to_invoice_qty(self):
        # Leased lines are invoiced separately from lease schedules
        leased = self.filtered(lambda line: line.is_lease)
        for line in leased:
            line.qty_to_invoice = 0.0

        return super(SaleOrderLine, self - leased)._get_to_invoice_qty()

    @api.depends(
        "state",
        "product_uom_qty",
        "qty_delivered",
        "qty_to_invoice",
        "qty_invoiced",
        "is_lease",
    )
    def _compute_invoice_status(self):
        # Leased lines are invoiced separately from lease schedules
        leased = self.filtered(lambda line: line.is_lease)
        leased.write(
            {
                "invoice_status": "no",
            }
        )
        return super(SaleOrderLine, self - leased)._compute_invoice_status()

    @api.depends("is_lease", "date_lease_start", "lease_pricing_id")
    def _compute_lease_end(self):
        for record in self:
            if (
                not record.is_lease
                or not record.date_lease_start
                or not record.lease_pricing_id
            ):
                record.date_lease_end = False
                continue

            record.date_lease_end = record.lease_pricing_id._compute_end_date(
                record.date_lease_start
            )

    def get_sale_order_line_multiline_description_sale(self, product):
        return (
            super().get_sale_order_line_multiline_description_sale(product)
            + self._get_lease_order_line_description()
        )

    def _get_lease_order_line_description(self):
        if not self.is_lease:
            return ""

        return "\n%s\n%s - %s" % (
            self.lease_pricing_id.display_name,
            format_date(self.env, self.date_lease_start),
            format_date(
                self.env,
                self.date_lease_end,
            ),
        )

    @api.onchange("is_lease", "date_lease_start", "lease_pricing_id")
    def _onchange_leasing_info(self):
        self.product_id_change()
        if self.is_lease and self.lease_pricing_id:
            self.price_unit = self.env["account.tax"]._fix_tax_included_price_company(
                self._get_display_price(self.product_id),
                self.product_id.taxes_id,
                self.tax_id,
                self.company_id,
            )

    def _get_display_price(self, product):
        if self.is_lease and self.lease_pricing_id:
            return self.lease_pricing_id.price
        else:
            return super()._get_display_price(product)

    def write(self, vals):
        res = super().write(vals)

        # ensure we update the leasing description
        if "is_lease" in vals or "lease_pricing_id" in vals:
            for record in self:
                record._onchange_leasing_info()

        return res

    @api.constrains("is_lease", "lease_pricing_id", "product_id")
    def _ensure_lease_pricing_applies_to(self):
        for record in self:
            if record.is_lease and not record.product_id.lease_ok:
                raise ValidationError(_("You cannot lease an unleasable product!"))

            if not record.is_lease:
                continue

            if not record.lease_pricing_id:
                raise ValidationError(_("Lease pricing is not set!"))

            if record.lease_pricing_id not in record.product_id._get_lease_price_rules(
                pricelist=record.order_id.pricelist_id
            ):
                raise ValidationError(
                    _("Lease pricing is not in valid list of price rules")
                )

    @api.depends(
        "invoice_lines.move_id.state",
        "invoice_lines.quantity",
        "untaxed_amount_to_invoice",
        "lease_schedule_ids.state",
    )
    def _get_invoice_qty(self):
        leased = self.filtered(
            lambda line: line.is_lease and line.state in ["sale", "done"]
        )

        for line in leased:
            qty_done = 0.0

            if line.lease_schedule_ids:
                qty_done = (line.product_uom_qty / len(line.lease_schedule_ids)) * len(
                    line.lease_schedule_ids.filtered(
                        lambda lease_line: lease_line.state == "done"
                    )
                )

            line.qty_invoiced = qty_done

        return super(SaleOrderLine, (self - leased))._get_invoice_qty()
