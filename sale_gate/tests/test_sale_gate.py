from odoo.exceptions import UserError
from odoo.tests import new_test_user, tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged("post_install", "-at_install")
class TestSaleGate(SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_model = cls.env["ir.model"]._get("sale.order")
        cls.approver = new_test_user(
            cls.env,
            login="sg_approver",
            name="SG Approver",
            groups="sales_team.group_sale_salesman",
        )
        cls.group = cls.env["res.groups"].create(
            {"name": "SG Approvers", "users": [(4, cls.approver.id)]}
        )
        cls.Rule = cls.env["gate.rule"]
        cls.Clearance = cls.env["gate.clearance"]

    def _order(self):
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
            }
        )
        return order

    def _rule(self, **vals):
        vals.setdefault("name", "Rule")
        vals.setdefault("model_id", self.sale_model.id)
        vals.setdefault("trigger", "on_confirm")
        vals.setdefault("condition", "always")
        return self.Rule.create(vals)

    def test_block_then_clear_then_confirm(self):
        self._rule(dismiss_group_id=self.group.id)
        order = self._order()

        order.action_confirm()
        self.assertNotEqual(order.state, "sale")
        self.assertEqual(order.gate_state, "blocked")

        self.Clearance.with_user(self.approver).create(
            {"hold_id": order.gate_hold_ids.id}
        )
        self.assertEqual(order.gate_state, "cleared")

        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_edits_never_blocked_while_gated(self):
        self._rule(dismiss_group_id=self.group.id)
        order = self._order()
        order.action_confirm()
        self.assertEqual(order.gate_state, "blocked")

        # The whole point vs tier_validation: the record stays fully editable.
        order.write({"note": "still editable"})
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 5,
            }
        )
        self.assertEqual(order.note, "still editable")
        self.assertEqual(len(order.order_line), 2)

    def test_absolute_block_raises(self):
        self._rule()  # no dismiss_group_id -> absolute
        order = self._order()
        with self.assertRaises(UserError), self.env.cr.savepoint():
            order.action_confirm()
        self.assertNotEqual(order.state, "sale")

    def test_out_of_scope_rule_proceeds(self):
        self._rule(
            dismiss_group_id=self.group.id,
            record_domain="[('amount_total', '>', 1000000.0)]",
        )
        order = self._order()
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        self.assertFalse(order.gate_hold_ids)
