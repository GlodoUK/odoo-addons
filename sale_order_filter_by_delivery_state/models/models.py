# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import float_is_zero


class SaleOrder(models.Model):
    _inherit = "sale.order"

    delivery_status = fields.Selection(
        [
            ("no", "No Information"),
            ("partial", "Partial"),
            ("complete", "Complete"),
            ("overcompleted", "Overcompleted"),
        ],
        string="Delivery Status",
        default="no",
        compute="_compute_delivery_Status",
        store=True,
        readonly=True,
    )

    @api.depends("state", "order_line.delivery_status")
    def _compute_delivery_Status(self):
        for order in self:
            # Ignore the status of the deposit product
            deposit_product_id = self.env[
                "sale.advance.payment.inv"
            ]._default_product_id()
            line_delivery_status = [
                line.delivery_status
                for line in order.order_line
                if line.product_id != deposit_product_id
            ]

            if order.state not in ("sale", "done"):
                order.delivery_status = "no"
            elif any(
                delivery_status == "partial" for delivery_status in line_delivery_status
            ):
                order.delivery_status = "partial"
            elif all(
                delivery_status == "complete"
                for delivery_status in line_delivery_status
            ):
                order.delivery_status = "complete"
            elif any(
                delivery_status == "overcompleted"
                for delivery_status in line_delivery_status
            ):
                order.delivery_status = "overcompleted"
            else:
                order.delivery_status = "no"


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    delivery_status = fields.Selection(
        [
            ("no", "No Information"),
            ("partial", "Partial"),
            ("complete", "Complete"),
            ("overcompleted", "Overcompleted"),
        ],
        string="Delivery Status",
        default="no",
        compute="_compute_delivery_status",
        store=True,
        readonly=True,
    )

    @api.depends("state", "product_uom_qty", "qty_delivered")
    def _compute_delivery_status(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for line in self:
            remaingin_qty = line.product_uom_qty - line.qty_delivered

            if line.state not in ("sale", "done"):
                line.delivery_status = "no"
            elif remaingin_qty > 0 and not float_is_zero(
                remaingin_qty, precision_digits=precision
            ):
                line.delivery_status = "partial"
            elif remaingin_qty < 0 and not float_is_zero(
                remaingin_qty, precision_digits=precision
            ):
                line.delivery_status = "overcompleted"
            else:
                line.delivery_status = "complete"


class SaleReport(models.Model):
    _inherit = "sale.report"

    delivery_status = fields.Selection(
        [
            ("no", "No Information"),
            ("partial", "Partial"),
            ("complete", "Complete"),
            ("overcompleted", "Overcompleted"),
        ],
        string="Delivery Status",
        readonly=True,
    )

    def _query(self, with_clause="", fields=None, groupby="", from_clause=""):
        if fields is None:
            fields = {}

        fields["delivery_status"] = ", s.delivery_status as delivery_status"
        groupby += ", s.delivery_status"
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
