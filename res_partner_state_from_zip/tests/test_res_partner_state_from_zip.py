from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestResPartnerStateFromZip(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Prefix = cls.env["res_partner_state_from_zip.prefix"]
        cls.uk = cls.env.ref("base.uk")
        cls.us = cls.env.ref("base.us")
        # Dev DB is a prod copy.
        cls.Prefix.search([("country_id", "in", (cls.uk + cls.us).ids)]).unlink()
        cls.area, cls.district, cls.other = (
            cls.env.ref("base.state_uk1"),
            cls.env.ref("base.state_uk2"),
            cls.env.ref("base.state_uk3"),
        )
        cls.california = cls.env.ref("base.state_us_5")
        cls.Prefix.create(
            [
                {"prefix": "b", "state_id": cls.area.id},
                {"prefix": "B1", "state_id": cls.district.id},
                {"prefix": "B11", "state_id": cls.other.id},
                {"prefix": "90", "state_id": cls.california.id},
            ]
        )

    def _partner(self, country, zip_code, **vals):
        return self.env["res.partner"].create(
            {"name": "Zip Test", "country_id": country.id, "zip": zip_code, **vals}
        )

    def test_gb_matches_longest_outcode_prefix(self):
        self.assertEqual(self._partner(self.uk, "b1 1aa").state_id, self.district)
        self.assertEqual(self._partner(self.uk, "B11 1AA").state_id, self.other)
        self.assertEqual(self._partner(self.uk, "B99 9ZZ").state_id, self.area)

    def test_other_countries_use_the_whole_zip(self):
        self.assertEqual(self._partner(self.us, "90210-1234").state_id, self.california)
        self.assertFalse(self._partner(self.us, "10001").state_id)

    def test_never_overwrites_a_state(self):
        partner = self._partner(self.uk, "B1 1AA", state_id=self.other.id)
        self.assertEqual(partner.state_id, self.other)
        partner.zip = "B99 9ZZ"
        self.assertEqual(partner.state_id, self.other)

    def test_never_overwrites_a_related_contacts_state(self):
        # Must not sync up over the parent's state.
        parent = self._partner(
            self.uk, "B1 1AA", is_company=True, state_id=self.other.id
        )
        child = self._partner(self.uk, "B1 1AA", parent_id=parent.id)
        child._update_address({"state_id": False})
        child.action_fill_state_from_zip()
        self.assertEqual(child.state_id, self.district)
        self.assertEqual(parent.state_id, self.other)

    def test_skip_context(self):
        partner = self.env["res.partner"].with_context(
            skip_res_partner_state_from_zip=True
        )
        partner = partner.create(
            {"name": "Zip Test", "country_id": self.uk.id, "zip": "B1 1AA"}
        )
        self.assertFalse(partner.state_id)
        partner.zip = "B11 1AA"
        self.assertFalse(partner.state_id)

    def test_fallback_country(self):
        param = "res_partner_state_from_zip.fallback_company_country"
        no_country = self.env["res.country"]
        # Dev DB is a prod copy, which sets this.
        self.env["ir.config_parameter"].set_param(param, False)
        self.assertFalse(self._partner(no_country, "B1 1AA").state_id)

        self.env["ir.config_parameter"].set_param(param, "True")
        self.env.company.country_id = self.uk
        partner = self._partner(no_country, "B1 1AA")
        self.assertEqual(partner.state_id, self.district)
        self.assertEqual(partner.country_id, self.uk)
        self.assertFalse(self._partner(no_country, "90210").country_id)
        self.assertEqual(self._partner(self.us, "90210").state_id, self.california)

    def test_write_fills_a_blank_state(self):
        partner = self._partner(self.uk, False)
        partner.zip = "B1 1AA"
        self.assertEqual(partner.state_id, self.district)

    def test_new_rule_is_used_straight_away(self):
        self.assertFalse(self._partner(self.uk, "CV1 1AA").state_id)
        self.Prefix.create({"prefix": "CV", "state_id": self.other.id})
        self.assertEqual(self._partner(self.uk, "CV1 1AA").state_id, self.other)
