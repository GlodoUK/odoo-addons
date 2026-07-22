from odoo_test_helper import FakeModelLoader

from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class GateCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .gate_tester import GateTestModel

        cls.loader.update_registry((GateTestModel,))

        cls.test_model = cls.env[GateTestModel._name]
        cls.ir_model = cls.env["ir.model"].search(
            [("model", "=", GateTestModel._name)]
        )
        cls.env["ir.model.access"].create(
            {
                "name": "access gate.test.model",
                "model_id": cls.ir_model.id,
                "perm_read": 1,
                "perm_write": 1,
                "perm_create": 1,
                "perm_unlink": 1,
            }
        )

        cls.Rule = cls.env["gate.rule"]
        cls.Clearance = cls.env["gate.clearance"]

        cls.approver = new_test_user(
            cls.env, login="gate_approver", name="Approver", groups="base.group_user"
        )
        cls.approver2 = new_test_user(
            cls.env, login="gate_approver2", name="Approver 2", groups="base.group_user"
        )
        cls.requester = new_test_user(
            cls.env, login="gate_requester", name="Requester", groups="base.group_user"
        )
        cls.group_a = cls.env["res.groups"].create(
            {
                "name": "Gate Test Group A",
                "users": [(4, cls.approver.id), (4, cls.approver2.id)],
            }
        )
        cls.group_b = cls.env["res.groups"].create(
            {"name": "Gate Test Group B", "users": [(4, cls.approver.id)]}
        )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    # -- helpers --

    def _rule(self, **vals):
        vals.setdefault("name", "Rule")
        vals.setdefault("model_id", self.ir_model.id)
        vals.setdefault("trigger", "manual")
        return self.Rule.create(vals)

    def _record(self, **vals):
        vals.setdefault("user_id", self.requester.id)
        return self.test_model.create(vals)

    def _clear(self, hold, user):
        return self.Clearance.with_user(user).create({"hold_id": hold.id})
