from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestCustomDisplayNameFormat(TransactionCase):
    def setUp(self):
        super().setUp()
        self.bank_id = self.env["res.bank"].create(
            {
                "name": "Test123",
                "bic": "456",
                "street": "street1",
                "street2": "street2",
                "city": "city",
                "zip": "zip",
            }
        )

        self.res_partner_bank_id = self.env["res.partner.bank"].create(
            {
                "bank_id": self.bank_id.id,
                "acc_number": "ACC#1",
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

    def test_trim_double_spaces(self):
        self.res_partner_bank_id.acc_number = False
        self.res_partner_bank_id.custom_display_name_format = (
            "TESTY TEST    %(acc_number)s %(bank_name)s"
        )

        self.assertEqual("TESTY TEST Test123", self.res_partner_bank_id.display_name)
        self.assertFalse(self.res_partner_bank_id.custom_display_name_format_warning)

    @mute_logger("odoo.addons.res_partner_bank_display_format.models.res_partner_bank")
    def test_recover_from_keyerror(self):
        self.res_partner_bank_id.acc_number = False
        self.res_partner_bank_id.custom_display_name_format = (
            "TESTY TEST    %(acc_number)s %(bank_name)s %(unknown)s"
        )

        self.assertEqual("False - Test123", self.res_partner_bank_id.display_name)
        self.assertTrue(
            len(self.res_partner_bank_id.custom_display_name_format_warning) > 0
        )

    def test_trusted_untrusted(self):
        self.res_partner_bank_id.custom_display_name_format = "%(acc_number)s"

        self.assertEqual(
            "ACC#1 untrusted",
            self.res_partner_bank_id.with_context(
                display_account_trust=True
            ).display_name,
        )

        self.res_partner_bank_id.allow_out_payment = True

        self.assertEqual(
            "ACC#1 trusted",
            self.res_partner_bank_id.with_context(
                display_account_trust=True
            ).display_name,
        )
        self.assertFalse(self.res_partner_bank_id.custom_display_name_format_warning)
