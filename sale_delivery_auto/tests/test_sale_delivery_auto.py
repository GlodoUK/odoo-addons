from odoo import Command
from odoo.tests import Form
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleDeliveryAuto(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # The development database is a copy of production, so the carriers it
        # already holds would decide "first available" for us.
        cls.env["delivery.carrier"].search([]).write({"active": False})

        cls.company = cls.env.company
        cls.uk = cls.env.ref("base.uk")
        cls.fr = cls.env.ref("base.fr")

        # Pin the currency so the price rules below are the whole story.
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "sale_delivery_auto tests",
                "currency_id": cls.company.currency_id.id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "sale_delivery_auto customer",
                "country_id": cls.uk.id,
                "zip": "LS1 1AA",
                "property_product_pricelist": cls.pricelist.id,
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "sale_delivery_auto widget",
                "default_code": "SDA-WIDGET",
                "type": "consu",
                "weight": 1.0,
                "list_price": 100.0,
            }
        )
        cls.service = cls.env["product.product"].create(
            {
                "name": "sale_delivery_auto service",
                "default_code": "SDA-SERVICE",
                "type": "service",
                "list_price": 50.0,
            }
        )

        # Two carriers charging per unit, so a rate is exact and moves with the
        # order. "first" sorts ahead of "second" on sequence.
        cls.carrier_first = cls._make_carrier("SDA First", sequence=1, unit_price=2.0)
        cls.carrier_second = cls._make_carrier("SDA Second", sequence=2, unit_price=5.0)

    @classmethod
    def _make_carrier(cls, name, sequence, unit_price, **vals):
        product = cls.env["product.product"].create(
            {
                "name": f"{name} delivery",
                "default_code": f"SDA-{name.replace(' ', '-').upper()}",
                "type": "service",
                "list_price": 0.0,
            }
        )
        return cls.env["delivery.carrier"].create(
            {
                "name": name,
                "sequence": sequence,
                "product_id": product.id,
                "delivery_type": "base_on_rule",
                "price_rule_ids": [
                    Command.create(
                        {
                            "variable": "quantity",
                            "operator": "<=",
                            "max_value": 10000.0,
                            "list_price": unit_price,
                            "variable_factor": "quantity",
                        }
                    )
                ],
                **vals,
            }
        )

    def _make_order(self, qty=3, product=None, **vals):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": (product or self.product).id,
                            "product_uom_qty": qty,
                        }
                    )
                ],
                **vals,
            }
        )

    def _delivery_line(self, order):
        return order.order_line.filtered("is_delivery")

    def _choose_carrier(self, order, carrier):
        """Choose a delivery method the way a user does: through the wizard."""
        wizard = (
            self.env["choose.delivery.carrier"]
            .with_context(default_order_id=order.id)
            .create({"order_id": order.id, "carrier_id": carrier.id})
        )
        wizard.update_price()
        wizard.button_confirm()
        return wizard

    def test_first_available_carrier_is_assigned(self):
        order = self._make_order()
        self.assertEqual(order.carrier_id, self.carrier_first)
        self.assertFalse(order.delivery_carrier_manual)

    def test_sequence_decides_which_carrier_wins(self):
        self.carrier_second.sequence = 0
        order = self._make_order()
        self.assertEqual(order.carrier_id, self.carrier_second)

    def test_unavailable_carrier_is_passed_over(self):
        self.carrier_first.country_ids = [Command.set(self.fr.ids)]
        order = self._make_order()
        self.assertEqual(order.carrier_id, self.carrier_second)

    def test_carrier_over_weight_limit_is_passed_over(self):
        self.carrier_first.max_weight = 2.0
        order = self._make_order(qty=3)
        self.assertEqual(order.carrier_id, self.carrier_second)

    def test_carrier_assigned_when_first_line_is_added(self):
        order = self.env["sale.order"].create(
            {"partner_id": self.partner.id, "pricelist_id": self.pricelist.id}
        )
        self.assertFalse(order.carrier_id)
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
            }
        )
        self.assertEqual(order.carrier_id, self.carrier_first)

    def test_service_only_order_gets_nothing(self):
        order = self._make_order(product=self.service)
        self.assertFalse(order.carrier_id)
        self.assertFalse(self._delivery_line(order))

    def test_order_going_all_service_and_back(self):
        order = self._make_order(qty=3)
        self.assertEqual(order.carrier_id, self.carrier_first)
        service_line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.service.id,
                "product_uom_qty": 1,
            }
        )
        # Nothing physical left to ship: carrier and shipping cost both go, but
        # that is us tidying up, not somebody choosing "no delivery method".
        order.order_line.filtered(lambda line: line.product_id == self.product).unlink()
        self.assertFalse(order.carrier_id)
        self.assertFalse(self._delivery_line(order))
        self.assertFalse(order.delivery_carrier_manual)
        # So putting goods back on the order picks a carrier again.
        service_line.unlink()
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
            }
        )
        self.assertEqual(order.carrier_id, self.carrier_first)
        self.assertEqual(self._delivery_line(order).price_unit, 4.0)

    def test_combo_only_order_gets_nothing(self):
        # A combo is not a service, so a "not a service" test would treat this
        # as shippable. Only `consu` actually ships.
        choice = self.env["product.combo"].create(
            {
                "name": "sale_delivery_auto combo choice",
                "combo_item_ids": [Command.create({"product_id": self.service.id})],
            }
        )
        combo = self.env["product.product"].create(
            {
                "name": "sale_delivery_auto combo",
                "default_code": "SDA-COMBO",
                "type": "combo",
                "combo_ids": [Command.set(choice.ids)],
            }
        )
        order = self._make_order(product=combo, qty=1)
        self.assertFalse(order.carrier_id)
        self.assertFalse(self._delivery_line(order))

    def test_zero_quantity_leaves_nothing_to_ship(self):
        order = self._make_order(qty=3)
        self.assertEqual(order.carrier_id, self.carrier_first)
        # Same test `delivery` applies when it weighs an order: no quantity, no
        # shipment, so no carrier and no cost line.
        order.order_line[0].product_uom_qty = 0
        self.assertFalse(order.carrier_id)
        self.assertFalse(self._delivery_line(order))
        # Tidying up is ours, so putting a quantity back picks a carrier again.
        self.assertFalse(order.delivery_carrier_manual)
        order.order_line[0].product_uom_qty = 5
        self.assertEqual(order.carrier_id, self.carrier_first)
        self.assertEqual(self._delivery_line(order).price_unit, 10.0)

    def test_writing_the_carrier_directly_is_not_a_choice(self):
        # Choosing the delivery method means the wizard. A bare write to
        # carrier_id - a script, a connector - is not that, so the selection is
        # free to answer over it.
        order = self._make_order(qty=3)
        order.carrier_id = self.carrier_second
        self.assertFalse(order.delivery_carrier_manual)
        self.assertEqual(order.carrier_id, self.carrier_first)
        order.carrier_id = False
        self.assertEqual(order.carrier_id, self.carrier_first)
        self.assertTrue(self._delivery_line(order))

    def test_carrier_reassessed_when_it_stops_being_available(self):
        order = self._make_order()
        self.assertEqual(order.carrier_id, self.carrier_first)
        self.carrier_first.country_ids = [Command.set(self.fr.ids)]
        # A trigger field changing re-runs the selection.
        order.partner_shipping_id = self.partner
        order.order_line[0].product_uom_qty = 4
        self.assertEqual(order.carrier_id, self.carrier_second)

    def test_manual_carrier_is_never_replaced(self):
        order = self._make_order()
        self._choose_carrier(order, self.carrier_second)
        self.assertTrue(order.delivery_carrier_manual)
        order.order_line[0].product_uom_qty = 7
        self.assertEqual(order.carrier_id, self.carrier_second)

    def test_manual_carrier_survives_becoming_unavailable(self):
        order = self._make_order()
        self._choose_carrier(order, self.carrier_second)
        self.carrier_second.country_ids = [Command.set(self.fr.ids)]
        order.order_line[0].product_uom_qty = 7
        self.assertEqual(order.carrier_id, self.carrier_second)

    def test_carrier_on_create_is_not_a_choice_on_its_own(self):
        # Same rule as a write: a carrier handed to create is not the wizard.
        order = self._make_order(carrier_id=self.carrier_second.id)
        self.assertEqual(order.carrier_id, self.carrier_first)
        self.assertFalse(order.delivery_carrier_manual)

    def test_create_can_state_the_choice_itself(self):
        # Which leaves the flag as the way for a connector to force a carrier.
        order = self._make_order(
            carrier_id=self.carrier_second.id, delivery_carrier_manual=True
        )
        self.assertEqual(order.carrier_id, self.carrier_second)
        order.order_line[0].product_uom_qty = 7
        self.assertEqual(order.carrier_id, self.carrier_second)

    def test_clearing_the_manual_flag_hands_control_back(self):
        order = self._make_order()
        self._choose_carrier(order, self.carrier_second)
        order.delivery_carrier_manual = False
        self.assertEqual(order.carrier_id, self.carrier_first)

    def test_wizard_marks_the_carrier_manual(self):
        order = self._make_order()
        self._choose_carrier(order, self.carrier_second)
        self.assertEqual(order.carrier_id, self.carrier_second)
        self.assertTrue(order.delivery_carrier_manual)
        self.assertEqual(len(self._delivery_line(order)), 1)

    def test_skip_context(self):
        order = (
            self.env["sale.order"]
            .with_context(skip_delivery_auto=True)
            .create(
                {
                    "partner_id": self.partner.id,
                    "pricelist_id": self.pricelist.id,
                    "order_line": [
                        Command.create(
                            {"product_id": self.product.id, "product_uom_qty": 3}
                        )
                    ],
                }
            )
        )
        self.assertFalse(order.carrier_id)
        self.assertFalse(self._delivery_line(order))

    def test_delivery_line_created_at_the_carrier_rate(self):
        order = self._make_order(qty=3)
        line = self._delivery_line(order)
        self.assertEqual(len(line), 1)
        self.assertEqual(line.product_id, self.carrier_first.product_id)
        self.assertEqual(line.price_unit, 6.0)

    def test_price_follows_the_quantity(self):
        order = self._make_order(qty=3)
        self.assertEqual(self._delivery_line(order).price_unit, 6.0)
        order.order_line.filtered(
            lambda line: not line.is_delivery
        ).product_uom_qty = 10
        self.assertEqual(self._delivery_line(order).price_unit, 20.0)

    def test_price_follows_a_manual_carrier(self):
        order = self._make_order(qty=3)
        self._choose_carrier(order, self.carrier_second)
        self.assertEqual(self._delivery_line(order).price_unit, 15.0)
        order.order_line.filtered(lambda line: not line.is_delivery).product_uom_qty = 4
        self.assertEqual(self._delivery_line(order).price_unit, 20.0)

    def test_only_ever_one_delivery_line(self):
        order = self._make_order(qty=3)
        self._choose_carrier(order, self.carrier_second)
        order.order_line.filtered(lambda line: not line.is_delivery).product_uom_qty = 4
        order.partner_shipping_id = self.partner
        self.assertEqual(len(self._delivery_line(order)), 1)

    def test_confirmed_order_is_left_alone(self):
        order = self._make_order(qty=3)
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        # Unrelated to this module: `sale` forbids editing quantities on a
        # locked order, and this company locks orders on confirmation.
        order.locked = False
        price = self._delivery_line(order).price_unit
        order.order_line.filtered(
            lambda line: not line.is_delivery
        ).product_uom_qty = 20
        self.assertEqual(self._delivery_line(order).price_unit, price)

    def test_lines_written_through_the_order_are_seen(self):
        # How the form, and most code, saves lines: one2many commands on the
        # order rather than a write on the line itself.
        order = self.env["sale.order"].create(
            {"partner_id": self.partner.id, "pricelist_id": self.pricelist.id}
        )
        order.write(
            {
                "order_line": [
                    Command.create(
                        {"product_id": self.product.id, "product_uom_qty": 3}
                    )
                ]
            }
        )
        self.assertEqual(order.carrier_id, self.carrier_first)
        self.assertFalse(order.delivery_carrier_manual)
        self.assertEqual(self._delivery_line(order).price_unit, 6.0)

        goods = order.order_line.filtered(lambda line: not line.is_delivery)
        order.write({"order_line": [Command.update(goods.id, {"product_uom_qty": 10})]})
        self.assertEqual(self._delivery_line(order).price_unit, 20.0)

        order.write({"order_line": [Command.delete(self._delivery_line(order).id)]})
        self.assertFalse(order.carrier_id)
        self.assertTrue(order.delivery_carrier_manual)
        self.assertFalse(self._delivery_line(order))

    def test_form_save_picks_a_carrier(self):
        with Form(self.env["sale.order"]) as form:
            form.partner_id = self.partner
            with form.order_line.new() as line:
                line.product_id = self.product
                line.product_uom_qty = 3
            # Nothing happens while the form is open: the carrier and its cost
            # line are decided by the save.
            self.assertFalse(form.carrier_id)
        order = form.record
        self.assertEqual(order.carrier_id, self.carrier_first)
        self.assertFalse(order.delivery_carrier_manual)
        self.assertEqual(self._delivery_line(order).price_unit, 6.0)
        # Which means the order still follows the goods on it.
        order.order_line.filtered(
            lambda line: not line.is_delivery
        ).product_uom_qty = 10
        self.assertEqual(self._delivery_line(order).price_unit, 20.0)

    def test_form_edit_of_a_saved_order_stays_automatic(self):
        order = self._make_order(qty=3)
        with Form(order) as form:
            with form.order_line.edit(0) as line:
                line.product_uom_qty = 10
        self.assertEqual(order.carrier_id, self.carrier_first)
        self.assertFalse(order.delivery_carrier_manual)
        self.assertEqual(self._delivery_line(order).price_unit, 20.0)

    def test_deleting_the_delivery_line_is_honoured(self):
        order = self._make_order(qty=3)
        self._delivery_line(order).unlink()
        self.assertFalse(order.carrier_id)
        self.assertTrue(order.delivery_carrier_manual)
        order.order_line[0].product_uom_qty = 8
        self.assertFalse(self._delivery_line(order))
