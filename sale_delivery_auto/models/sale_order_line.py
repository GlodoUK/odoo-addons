from odoo import api, models

from .sale_order import IN_ORDER_WRITE, SKIP

# Line fields whose change moves the shipping cost: carriers rate on weight,
# volume and order value, and free_over on the order total.
LINE_TRIGGERS = frozenset(
    {
        "discount",
        "price_unit",
        "product_id",
        "product_uom_id",
        "product_uom_qty",
        "tax_ids",
    }
)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _delivery_auto_muted(self):
        # sale_write_from_compute is `sale` recomputing a price off the back of a
        # change we have already been told about. IN_ORDER_WRITE is a write on
        # the order carrying these lines as one2many commands: it answers for
        # them itself, once, rather than once per command.
        context = self.env.context
        return bool(
            context.get(SKIP)
            or context.get(IN_ORDER_WRITE)
            or context.get("sale_write_from_compute")
        )

    def _delivery_auto_orders(self):
        # The shipping cost line is our own output; a change to it says nothing
        # about what the carrier should charge.
        return self.filtered(lambda line: not line.is_delivery).order_id

    @api.model_create_multi
    def create(self, vals_list):
        muted = self._delivery_auto_muted()
        lines = super(SaleOrderLine, self.with_context(**{SKIP: True})).create(
            vals_list
        )
        # Back to the caller's environment: SKIP riding out on the returned
        # lines would mute every later write on them.
        lines = lines.with_env(self.env)
        if not muted:
            lines._delivery_auto_orders()._delivery_auto_run()
        return lines

    def write(self, vals):
        muted = self._delivery_auto_muted()
        orders = self._delivery_auto_orders()
        res = super(SaleOrderLine, self.with_context(**{SKIP: True})).write(vals)
        if not muted and set(vals) & LINE_TRIGGERS:
            orders._delivery_auto_run()
        return res

    def unlink(self):
        muted = self._delivery_auto_muted()
        orders = self._delivery_auto_orders()
        dropped = self.filtered("is_delivery").order_id
        # Muted throughout: `delivery` clears carrier_id from inside unlink(),
        # before the rows go, and letting that write re-run us mid-unlink would
        # remove the shipping cost line a second time.
        res = super(SaleOrderLine, self.with_context(**{SKIP: True})).unlink()
        dropped = dropped.exists()
        # Losing the shipping cost line takes the carrier with it, so read that
        # as "no delivery method, thank you" rather than putting the line
        # straight back. Recorded even under IN_ORDER_WRITE, where the order is
        # about to ask us for an answer - but not under SKIP, which is us
        # tidying up after an order with nothing left to ship, and callers who
        # asked to be left alone.
        if not self.env.context.get(SKIP):
            dropped.with_context(**{SKIP: True}).delivery_carrier_manual = True
        if muted:
            return res
        (orders.exists() - dropped)._delivery_auto_run()
        return res
