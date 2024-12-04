from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_can_checkout(self):
        self.ensure_one()
        return self.website_order_line

    def _cart_find_product_line(self, product_id=None, line_id=None, **kwargs):
        self.ensure_one()
        lines = super()._cart_find_product_line(product_id, line_id, **kwargs)
        # if we've been asked for a specific line, we must use that
        if line_id:
            return lines

        # if we have a lease, find the line which is_lease = True and the
        # lease_pricing_id matches
        if kwargs.get("lease"):
            lease_id = int(kwargs.get("lease"))
            return lines.filtered(
                lambda line: line.lease_pricing_id.id == lease_id and line.is_lease
            )

        # otherwise just find any line which isn't a leasing line
        return lines.filtered(lambda line: not line.is_lease)

    def _cart_update(
        self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs
    ):
        res = super()._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            **kwargs,
        )

        line_id = self.env["sale.order.line"].browse(res["line_id"])

        if "lease" in kwargs and line_id.exists():
            lease_id = self.env["sale_lease_stock.pricing"]
            lease = False
            if kwargs.get("lease"):
                lease = True
                lease_id = self.env["sale_lease_stock.pricing"].search(
                    [("id", "=", kwargs.get("lease"))], limit=1
                )

            to_change = {"is_lease": lease}
            if lease_id:
                to_change.update(
                    {
                        "lease_pricing_id": lease_id.id,
                    }
                )

            line_id.write(to_change)

        if line_id.exists() and line_id.is_lease:
            line_id.price_unit = line_id._get_display_price(line_id.product_id)
            # line_id.order_id._compute_website_order_line()

        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("product_id.display_name", "is_lease")
    def _compute_name_short(self):
        super()._compute_name_short()

        for record in self.filtered(lambda line: line.is_lease):
            record.name_short = "{} ({} {})".format(
                record.name_short,
                record.lease_pricing_id.duration,
                record.lease_pricing_id.unit,
            )
