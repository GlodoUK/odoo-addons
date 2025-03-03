from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPermissions(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.invoice = cls.init_invoice(
            "in_invoice", products=cls.product_a + cls.product_b
        )

    def test_without_permission(self):
        self.env.user.groups_id -= self.env.ref(
            "account_move_restrict_reset_to_draft.group_account_move_button_draft"
        )

        self.invoice.action_post()
        with self.assertRaises(UserError):
            self.invoice.button_draft()

    def test_with_permission(self):
        self.env.user.groups_id += self.env.ref(
            "account_move_restrict_reset_to_draft.group_account_move_button_draft"
        )

        self.invoice.action_post()
        self.invoice.button_draft()
