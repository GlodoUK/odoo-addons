from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestProductFsc(TransactionCase):
    def test_type_display_name(self):
        w1 = self.env.ref("product_fsc.fsc_category_w1")
        self.assertEqual(w1.display_name, "[W1] Rough wood")

    def test_type_search_by_code(self):
        types = self.env["product_fsc.type"].name_search("W8.2.3")
        self.assertIn(
            self.env.ref("product_fsc.fsc_category_w8_2_3").id,
            [type_id for type_id, _name in types],
        )

    def test_type_hierarchy(self):
        w8 = self.env.ref("product_fsc.fsc_category_w8")
        osb = self.env.ref("product_fsc.fsc_category_w8_2_3")
        children = self.env["product_fsc.type"].search([("id", "child_of", w8.id)])
        self.assertIn(osb, children)

    def test_type_recursion(self):
        w1 = self.env.ref("product_fsc.fsc_category_w1")
        with self.assertRaises(ValidationError):
            w1.parent_id = self.env.ref("product_fsc.fsc_category_w1_1")

    def test_type_code_unique_per_standard(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            self.env["product_fsc.type"].create({"code": "W1", "name": "Duplicate"})
            self.env.flush_all()

    def test_label(self):
        product = self.env["product.template"].create(
            {
                "name": "FSC Board",
                "fsc_certified": True,
                "fsc_classification": "fsc_mix",
                "fsc_percentage": 0.7,
            }
        )
        self.assertEqual(product.fsc_label, "FSC Mix 70%")
        product.fsc_classification = "fsc_controlled_wood"
        self.assertEqual(product.fsc_label, "FSC Controlled Wood")
