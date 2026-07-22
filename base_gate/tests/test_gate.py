from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import GateCommon


@tagged("post_install", "-at_install")
class TestGate(GateCommon):
    def test_no_rules_proceeds(self):
        record = self._record(amount=100.0)
        record.action_confirm()
        self.assertTrue(record.confirmed)
        self.assertEqual(record.gate_state, "open")

    def test_routable_block_holds_then_clears(self):
        self._rule(dismiss_group_id=self.group_a.id, condition="always")
        record = self._record(amount=100.0)

        record.action_confirm()
        # blocked, not confirmed, one pending hold
        self.assertFalse(record.confirmed)
        self.assertEqual(record.gate_state, "blocked")
        self.assertEqual(len(record.gate_hold_ids), 1)
        self.assertEqual(record.gate_hold_ids.state, "pending")

        # an authorised, non-requester approver clears it
        self._clear(record.gate_hold_ids, self.approver)
        self.assertEqual(record.gate_hold_ids.state, "cleared")
        self.assertEqual(record.gate_state, "cleared")

        # now it confirms
        record.action_confirm()
        self.assertTrue(record.confirmed)

    def test_absolute_block_raises(self):
        self._rule(condition="always")  # no dismiss_group_id -> absolute
        record = self._record(amount=100.0)
        with self.assertRaises(UserError), self.env.cr.savepoint():
            record.action_confirm()
        self.assertFalse(record.confirmed)

    def test_self_clearance_blocked(self):
        self._rule(dismiss_group_id=self.group_a.id, condition="always")
        # requester is also an approver group member
        self.group_a.write({"users": [(4, self.requester.id)]})
        record = self._record(amount=100.0, user_id=self.requester.id)
        record.action_confirm()
        with self.assertRaises(UserError), self.env.cr.savepoint():
            self._clear(record.gate_hold_ids, self.requester)

    def test_self_clearance_allowed_when_flagged(self):
        self._rule(
            dismiss_group_id=self.group_a.id, condition="always", allow_self=True
        )
        self.group_a.write({"users": [(4, self.requester.id)]})
        record = self._record(amount=100.0, user_id=self.requester.id)
        record.action_confirm()
        self._clear(record.gate_hold_ids, self.requester)
        self.assertEqual(record.gate_state, "cleared")

    def test_unauthorised_user_cannot_clear(self):
        self._rule(dismiss_group_id=self.group_a.id, condition="always")
        record = self._record(amount=100.0)
        record.action_confirm()
        # requester is not in group_a
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self._clear(record.gate_hold_ids, self.requester)

    def test_waterfall_tiers(self):
        self._rule(
            name="Tier 10", sequence=10, dismiss_group_id=self.group_a.id,
            condition="always",
        )
        self._rule(
            name="Tier 20", sequence=20, dismiss_group_id=self.group_b.id,
            condition="always",
        )
        record = self._record(amount=100.0)
        record.action_confirm()

        holds = record.gate_hold_ids.sorted("tier")
        self.assertEqual(holds.mapped("state"), ["pending", "waiting"])

        # cannot clear the waiting (higher) tier first
        with self.assertRaises(UserError), self.env.cr.savepoint():
            self._clear(holds[1], self.approver)

        # clear tier 10 -> tier 20 activates
        self._clear(holds[0], self.approver)
        self.assertEqual(holds.mapped("state"), ["cleared", "pending"])

        # clear tier 20 -> all cleared, confirms
        self._clear(holds[1], self.approver)
        self.assertEqual(record.gate_state, "cleared")
        record.action_confirm()
        self.assertTrue(record.confirmed)

    def test_dynamic_reevaluation_on_edit(self):
        # rule applies only to records over 100
        self._rule(
            dismiss_group_id=self.group_a.id,
            condition="always",
            record_domain="[('amount', '>', 100.0)]",
        )
        record = self._record(amount=50.0)
        record.action_confirm()
        self.assertTrue(record.confirmed)  # not in scope, proceeds
        self.assertFalse(record.gate_hold_ids)

        # push it into scope -> hold materialises on write, no edit block
        record.write({"amount": 200.0})
        self.assertEqual(len(record.gate_hold_ids), 1)
        self.assertEqual(record.gate_state, "blocked")

        # pull it back out of scope -> hold resolves
        record.write({"amount": 50.0})
        self.assertFalse(record.gate_hold_ids)

    def test_min_dismissals_requires_two(self):
        self._rule(
            dismiss_group_id=self.group_a.id, condition="always", min_dismissals=2
        )
        record = self._record(amount=100.0)
        record.action_confirm()
        hold = record.gate_hold_ids

        self._clear(hold, self.approver)
        self.assertEqual(hold.state, "pending")  # one of two
        self._clear(hold, self.approver2)
        self.assertEqual(hold.state, "cleared")

    def test_code_condition(self):
        self._rule(
            dismiss_group_id=self.group_a.id,
            condition="code",
            code="raise_gate = record.amount > 500",
        )
        low = self._record(amount=100.0)
        low.action_confirm()
        self.assertTrue(low.confirmed)

        high = self._record(amount=1000.0)
        high.action_confirm()
        self.assertFalse(high.confirmed)
        self.assertEqual(high.gate_state, "blocked")

    def test_officer_force_clears_absolute_block(self):
        self._rule(condition="always")  # absolute, no group
        officer = self.env.ref("base_gate.group_gate_officer")
        officer.write({"users": [(4, self.approver.id)]})
        record = self._record(amount=100.0)
        # absolute block cannot even be confirmed to create a hold; sync directly
        record._sync_gates(["manual"])
        self.assertTrue(record.gate_hold_ids)
        # officer force-clears despite no dismiss group
        self._clear(record.gate_hold_ids, self.approver)
        self.assertEqual(record.gate_state, "cleared")
