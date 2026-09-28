import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Callers set this to keep us out of a whole flow (imports, connectors, data
# migrations). We also set it on ourselves while working, so the writes we make
# do not come back in through create/write/unlink.
SKIP = "skip_delivery_auto"

# Set while a write on the order is in flight, so the hooks on sale.order.line
# stay quiet for the one2many commands it carries: the order answers for its own
# lines once, from the top, rather than once per command. Deliberately not SKIP -
# a shipping cost line deleted this way is still somebody deleting it, and the
# line hook has to be able to tell that from our own tidying up.
IN_ORDER_WRITE = "delivery_auto_in_order_write"

# Order fields whose change makes the carrier choice, or the shipping cost,
# stale. In code on purpose: this is not something to hand to a user.
ORDER_TRIGGERS = frozenset(
    {
        "carrier_id",
        "company_id",
        "currency_id",
        "date_order",
        "delivery_carrier_manual",
        "fiscal_position_id",
        # Lines arriving as one2many commands inside a write on the order - how
        # the form, and most code, saves them - go in with our own context on,
        # so the hooks on sale.order.line stay quiet for them. The order has to
        # answer for its own lines.
        "order_line",
        "partner_id",
        "partner_shipping_id",
        "pricelist_id",
        "warehouse_id",
    }
)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    delivery_carrier_manual = fields.Boolean(
        string="Delivery Method Chosen Manually",
        help="The delivery method on this order was chosen by hand, so it is "
        "never replaced automatically. Untick to hand the choice back to the "
        "automatic selection.",
    )

    def _delivery_auto_stopped(self):
        context = self.env.context
        return bool(context.get(SKIP) or context.get(IN_ORDER_WRITE))

    def _delivery_auto_editable(self):
        self.ensure_one()
        return self.state in ("draft", "sent")

    def _delivery_auto_has_goods(self):
        self.ensure_one()
        return bool(
            self.order_line.filtered(
                lambda line: (
                    line.product_id.type == "consu"
                    and line.product_uom_qty > 0
                    and not line.display_type
                    and not line.is_delivery
                )
            )
        )

    def _delivery_auto_pick_carrier(self):
        self.ensure_one()
        order = self.with_company(self.company_id)
        model = self.env["delivery.carrier"]
        # delivery.carrier is ordered by sequence, so "the first available one"
        # follows the list as it reads in the UI.
        carriers = model.search(model._check_company_domain(self.company_id))
        return carriers.available_carriers(order.partner_shipping_id, order)[:1]

    def _delivery_auto_set_carrier(self):
        for order in self:
            if (
                order.delivery_carrier_manual
                or not order._delivery_auto_editable()
                or not order._delivery_auto_has_goods()
            ):
                continue
            carrier = order._delivery_auto_pick_carrier()
            if carrier != order.carrier_id:
                # Say so explicitly: writing carrier_id without this is what
                # marks a delivery method as chosen by hand.
                order.write(
                    {
                        "carrier_id": carrier.id,
                        "delivery_carrier_manual": False,
                    }
                )

    def _delivery_auto_line_vals(self, line, price_unit):
        """Values to sync onto an existing shipping cost line."""
        self.ensure_one()
        vals = self._prepare_delivery_line_vals(self.carrier_id, price_unit)
        # These say where the line lives, not what it costs.
        vals.pop("order_id", None)
        vals.pop("sequence", None)
        # Leave a hand-written description alone unless the carrier changed.
        if line.product_id == self.carrier_id.product_id:
            vals.pop("name", None)
        # `sale` reads price_unit drifting from technical_price_unit as "a human
        # typed this in" and stops recomputing the line. Move them together.
        vals["technical_price_unit"] = vals["price_unit"]
        return vals

    def _delivery_auto_refresh_price(self):
        self.ensure_one()
        if not self._delivery_auto_editable():
            return
        line = self.order_line.filtered("is_delivery")[:1]
        if not self._delivery_auto_has_goods():
            # Nothing ships, so there is nothing to charge for. `delivery`
            # clears carrier_id as the line goes and that write would read as a
            # manual choice, so state the outcome ourselves: this tidy-up is
            # ours, not somebody's decision.
            if line or self.carrier_id:
                self.write({"carrier_id": False, "delivery_carrier_manual": False})
            if line:
                self._remove_delivery_line()
            return
        if not self.carrier_id:
            # Somebody cleared the delivery method. Drop the cost line with it
            # and leave that choice standing.
            if line:
                self._remove_delivery_line()
            return
        rate = self.carrier_id.rate_shipment(self)
        if not rate.get("success"):
            _logger.info(
                "%s: %s could not rate this order: %s",
                self.display_name,
                self.carrier_id.display_name,
                rate.get("error_message"),
            )
            # Never block the save over this; flag it for the "Update shipping
            # cost" button instead.
            self.write(
                {
                    "delivery_message": rate.get("error_message") or False,
                    "recompute_delivery_price": True,
                }
            )
            return
        if line:
            line.write(self._delivery_auto_line_vals(line, rate["price"]))
        else:
            self._create_delivery_line(self.carrier_id, rate["price"])
        self.write(
            {
                "delivery_message": rate.get("warning_message") or False,
                "recompute_delivery_price": False,
            }
        )

    def _delivery_auto_run(self):
        for order in self.with_context(**{SKIP: True}):
            order._delivery_auto_set_carrier()
            order._delivery_auto_refresh_price()

    def _prepare_delivery_line_vals(self, carrier, price_unit):
        vals = super()._prepare_delivery_line_vals(carrier, price_unit)
        # XXX: Pin the uom, it would otherwise be recomputed from the product and
        # we get stuck in a loop
        vals["product_uom_id"] = carrier.product_id.uom_id.id
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        orders = super(SaleOrder, self.with_context(**{IN_ORDER_WRITE: True})).create(
            vals_list
        )
        # Hand the caller back records in the caller's own environment: our
        # context is for the create in flight, and going out on the returned
        # recordset would quietly mute every later write on it - and on its
        # lines, which inherit it.
        orders = orders.with_env(self.env)
        if not self._delivery_auto_stopped():
            orders._delivery_auto_run()
        return orders

    def write(self, vals):
        res = super(SaleOrder, self.with_context(**{IN_ORDER_WRITE: True})).write(vals)
        if not self._delivery_auto_stopped() and set(vals) & ORDER_TRIGGERS:
            self._delivery_auto_run()
        return res

    def set_delivery_line(self, carrier, amount):
        # Somebody choosing the delivery method outright - the "Add shipping"
        # wizard, a customer picking one at checkout - is the one thing that
        # marks a carrier as chosen by hand. Muted while it happens: the carrier
        # and the price are the caller's, and we are not to answer over them.
        orders = self.with_context(**{SKIP: True})
        res = super(SaleOrder, orders).set_delivery_line(carrier, amount)
        orders.delivery_carrier_manual = True
        return res

    def action_confirm(self):
        # XXX: Last chance to get a carrier and a shipping cost onto the order.
        if not self._delivery_auto_stopped():
            self._delivery_auto_run()
        return super().action_confirm()
