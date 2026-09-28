from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_is_zero, float_repr


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    force_moq = fields.Boolean(
        "Override MOQ",
        tracking=True,
        copy=False,
    )

    def button_confirm(self):
        todo = self.filtered(lambda x: x.state in ("draft", "sent"))
        todo.order_line._check_moq()
        return super().button_confirm()


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _check_moq(self):
        precision = self.env["decimal.precision"].precision_get("Product Unit")

        for line in self.filtered(
            lambda r: (
                r.product_id
                and not float_is_zero(r.product_uom_qty, precision_digits=precision)
            )
        ):
            if line.order_id.force_moq:
                continue

            seller_id = line.selected_seller_id

            if not seller_id:
                # quit early
                if not line.product_id.seller_ids:
                    continue

                seller_id = line.product_id._select_seller(
                    partner_id=line.partner_id, quantity=0.0, uom_id=line.product_uom_id
                )

            if not seller_id:
                # Fallback to the first appropriate seller_id
                seller_id = next(
                    iter(
                        line.product_id.seller_ids.filtered(
                            lambda x, line=line: (
                                x.partner_id == line.partner_id
                                and (
                                    x.product_uom_id.relative_uom_id or x.product_uom_id
                                )
                                == (
                                    line.product_uom_id.relative_uom_id
                                    or line.product_uom_id
                                )
                            )
                        )
                    ),
                    self.env["product.supplierinfo"],
                )

            if not seller_id:
                continue

            if float_is_zero(seller_id.moq, precision_digits=precision):
                continue

            quantity_uom_seller = line.product_uom_id._compute_quantity(
                line.product_qty,
                seller_id.product_uom_id,
            )

            if (
                float_compare(
                    quantity_uom_seller, seller_id.moq, precision_digits=precision
                )
                < 0
            ):
                raise ValidationError(
                    self.env._(
                        "You cannot purchase less than the minimum quantity of "
                        "%(moq)s %(uom)s for %(product_id)s from %(partner_id)s",
                        moq=float_repr(seller_id.moq, precision_digits=precision),
                        uom=seller_id.product_uom_id.name,
                        product_id=line.product_id.name,
                        partner_id=line.partner_id.name,
                    )
                )
