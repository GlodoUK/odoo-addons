from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDisplayNameRef(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        ResPartner = cls.env["res.partner"]

        cls.partnerA = ResPartner.create(
            {
                "name": "Partner A",
                "ref": "Reference A",
            }
        )

        cls.partnerB = ResPartner.create(
            {
                "name": "Partner B",
                "ref": "Reference B",
                "parent_id": cls.partnerA.id,
            }
        )

        cls.partnerC = ResPartner.create(
            {
                "name": "Partner C",
                "ref": "Reference C",
                "type": "delivery",
                "parent_id": cls.partnerB.id,
            }
        )

    def test_compute_display_name_01(self):
        self.assertEqual(
            self.partnerA.display_name,
            "[Reference A] Partner A",
        )

    def test_compute_display_name_02(self):
        display_name = self.partnerB.display_name

        self.assertEqual(
            display_name.count("["),
            1,
        )

        self.assertEqual(
            display_name.count("]"),
            1,
        )

        self.assertIn("[Reference B]", display_name)

    def test_compute_display_name_03(self):
        display_name = self.partnerC.display_name

        self.assertEqual(
            display_name.count("["),
            1,
        )

        self.assertEqual(
            display_name.count("]"),
            1,
        )

        self.assertIn("[Reference C]", display_name)

    # Idempotency Check
    def test_compute_display_name_04(self):
        self.assertEqual(
            self.partnerA.display_name,
            "[Reference A] Partner A",
        )

        self.partnerA._compute_display_name()

        self.assertEqual(
            self.partnerA.display_name,
            "[Reference A] Partner A",
        )
