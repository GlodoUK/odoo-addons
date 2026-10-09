from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestCustomDisplayNameFormat(TransactionCase):
    def setUp(self):
        super().setUp()
        self.res_partner_bank_id = self.env["res.partner.bank"].create(
            {
                "account_number": "ACC#1",
                "bank_name": "Test123",
                "bank_bic": "456",
                "street": "street1",
                "street2": "street2",
                "city": "city",
                "zip": "zip",
                "partner_id": self.env.company.partner_id.id,
                "custom_display_name_format": (
                    "TESTY TEST %(acc_number)s %(bank_name)s %(bank_street)s"
                    " %(bank_street2)s %(bank_city)s %(bank_zip)s"
                ),
            }
        )

    def test_custom_format(self):
        self.assertEqual(
            "TESTY TEST ACC#1 Test123 street1 street2 city zip",
            self.res_partner_bank_id.display_name,
        )
        self.assertFalse(self.res_partner_bank_id.custom_display_name_format_warning)

    def test_account_number_key(self):
        self.res_partner_bank_id.custom_display_name_format = (
            "%(account_number)s / %(acc_number)s / %(bank_bic)s"
        )

        self.assertEqual("ACC#1 / ACC#1 / 456", self.res_partner_bank_id.display_name)
        self.assertFalse(self.res_partner_bank_id.custom_display_name_format_warning)

    def test_trim_double_spaces(self):
        self.res_partner_bank_id.street2 = False
        self.res_partner_bank_id.custom_display_name_format = (
            "TESTY TEST    %(bank_street2)s %(bank_name)s"
        )

        self.assertEqual("TESTY TEST Test123", self.res_partner_bank_id.display_name)
        self.assertFalse(self.res_partner_bank_id.custom_display_name_format_warning)

    @mute_logger("odoo.addons.res_partner_bank_display_format.models.res_partner_bank")
    def test_recover_from_keyerror(self):
        self.res_partner_bank_id.custom_display_name_format = (
            "TESTY TEST    %(acc_number)s %(bank_name)s %(unknown)s"
        )

        self.assertEqual("ACC#1 - Test123", self.res_partner_bank_id.display_name)
        self.assertTrue(
            len(self.res_partner_bank_id.custom_display_name_format_warning) > 0
        )
