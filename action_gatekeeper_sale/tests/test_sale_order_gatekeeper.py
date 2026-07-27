from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleOrderGatekeeper(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.SaleOrder = cls.env["sale.order"]
        cls.GatekeeperRule = cls.env["gatekeeper.rule"]

        cls.partner = cls.env["res.partner"].create({"name": "Gatekeeper Partner"})
        cls.other_partner = cls.env["res.partner"].create({"name": "Other Partner"})
        cls.product = cls.env["product.product"].create({"name": "Gatekeeper Product"})

        cls.trigger_create = cls.env.ref("action_gatekeeper.gatekeeper_trigger_create")
        cls.trigger_write = cls.env.ref("action_gatekeeper.gatekeeper_trigger_write")
        cls.trigger_confirm = cls.env.ref(
            "action_gatekeeper_sale.gatekeeper_trigger_action_confirm"
        )

    def _make_rule(self, action, trigger=None, rule="always", **extra):
        return self.GatekeeperRule.create(
            {
                "name": "Sale Gatekeeper Rule",
                "target_model": "sale.order",
                "trigger": (trigger or self.trigger_create).id,
                "rule": rule,
                "action": action,
                **extra,
            }
        )

    def _make_order(self, partner=None):
        return self.SaleOrder.create(
            {
                "partner_id": (partner or self.partner).id,
                "order_line": [
                    Command.create(
                        {"product_id": self.product.id, "product_uom_qty": 1}
                    )
                ],
            }
        )

    def test_always_block_prevents_create(self):
        self._make_rule(action="block")
        with self.assertRaises(ValidationError):
            self._make_order()

    def test_always_hold_sets_hold_and_creates_line(self):
        rule = self._make_rule(action="hold")
        order = self._make_order()
        self.assertTrue(order.gatekeeper_hold)
        self.assertEqual(order.gatekeeper_rule_lines.rule_id, rule)

    def test_releasing_all_lines_clears_hold(self):
        self._make_rule(action="hold")
        order = self._make_order()
        line = order.gatekeeper_rule_lines
        line.action_release()
        self.assertTrue(line.is_released)
        self.assertFalse(order.gatekeeper_hold)

    def test_no_matching_rule_does_not_hold_or_block(self):
        self._make_rule(action="block", trigger=self.trigger_write)
        order = self._make_order()
        self.assertFalse(order.gatekeeper_hold)

    def test_partner_domain_rule_matches_partner(self):
        self._make_rule(
            action="block",
            rule="partner_domain",
            partner_domain=f"[('id', '=', {self.partner.id})]",
        )
        with self.assertRaises(ValidationError):
            self._make_order(partner=self.partner)
        # A different partner does not match the domain.
        self._make_order(partner=self.other_partner)

    def test_record_domain_rule_matches_record(self):
        self._make_rule(
            action="block",
            rule="record_domain",
            record_domain=f"[('partner_id', '=', {self.partner.id})]",
        )
        with self.assertRaises(ValidationError):
            self._make_order(partner=self.partner)
        self._make_order(partner=self.other_partner)

    def test_code_rule_evaluates_trigger_rule(self):
        self._make_rule(
            action="block",
            rule="code",
            code=f"trigger_rule = record_id.partner_id.id == {self.partner.id}",
        )
        with self.assertRaises(ValidationError):
            self._make_order(partner=self.partner)
        self._make_order(partner=self.other_partner)

    def test_action_confirm_trigger_holds_on_confirm_not_create(self):
        self._make_rule(action="hold", trigger=self.trigger_confirm)
        order = self._make_order()
        self.assertFalse(order.gatekeeper_hold)
        order.action_confirm()
        self.assertTrue(order.gatekeeper_hold)
