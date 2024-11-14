import uuid

from odoo.addons.cpq.tests.common import TestCpqCommon

COW_PRINT = "Cow Print"


class TestOneAttributeVariantCreation(TestCpqCommon):
    def setUp(self):
        super().setUp()

        self.variant_creation_vals = {
            "name": "Chair",
            "type": "consu",
            "cpq_ok": False,
            "attribute_line_ids": [
                (
                    0,
                    0,
                    {
                        "attribute_id": self.prod_attrib_colour.id,
                        "value_ids": [
                            (
                                6,
                                0,
                                [
                                    self.prod_attrib_colour_red.id,
                                    self.prod_attrib_colour_blue.id,
                                    self.prod_attrib_colour_green.id,
                                    self.prod_attrib_colour_custom.id,
                                ],
                            )
                        ],
                    },
                )
            ],
        }

    def test_variants_exist_when_not_cpq_ok(self):
        # When cpq_ok = False, ensure that we have not broken
        ProductTemplate = self.env["product.template"]

        vals = self.variant_creation_vals.copy()
        vals.update(
            {
                "cpq_ok": False,
            }
        )
        product_tmpl_id = ProductTemplate.create(vals)

        self.assertTrue(product_tmpl_id.product_variant_ids)
        self.assertTrue(len(product_tmpl_id.product_variant_ids) == 4)

    def test_no_variants_exist_when_cpq_ok(self):
        ProductTemplate = self.env["product.template"]

        vals = self.variant_creation_vals.copy()
        vals.update(
            {
                "cpq_ok": True,
            }
        )
        product_tmpl_id = ProductTemplate.create(vals)

        self.assertFalse(product_tmpl_id.product_variant_ids)
        self.assertTrue(len(product_tmpl_id.product_variant_ids) == 0)

    def test_cpq_variant_creation(self):
        ProductTemplate = self.env["product.template"]

        vals = self.variant_creation_vals.copy()
        vals.update(
            {
                "cpq_ok": True,
            }
        )
        product_tmpl_id = ProductTemplate.create(vals)

        ptav_ids = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_attribute_value_id", "=", self.prod_attrib_colour_red.id),
            ],
            limit=1,
        )

        variant_id = product_tmpl_id._cpq_get_create_variant(
            ptav_ids,
            None,
        )
        self.assertTrue(variant_id.cpq_ok)
        self.assertEqual(variant_id.product_tmpl_id, product_tmpl_id)
        self.assertFalse(variant_id.cpq_custom_value_ids)
        self.assertEqual(variant_id.product_template_attribute_value_ids, ptav_ids)
        self.assertEqual(len(product_tmpl_id.product_variant_ids), 1)

    def test_cpq_variant_reuse(self):
        ProductTemplate = self.env["product.template"]

        vals = self.variant_creation_vals.copy()
        vals.update(
            {
                "cpq_ok": True,
            }
        )
        product_tmpl_id = ProductTemplate.create(vals)

        ptav_ids = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_attribute_value_id", "=", self.prod_attrib_colour_red.id),
            ],
            limit=1,
        )

        variant_id = product_tmpl_id._cpq_get_create_variant(
            ptav_ids,
            None,
        )
        self.assertEqual(variant_id.product_template_attribute_value_ids, ptav_ids)
        self.assertEqual(len(product_tmpl_id.product_variant_ids), 1)

        reused_variant_id = product_tmpl_id._cpq_get_create_variant(
            ptav_ids,
            None,
        )

        self.assertEqual(
            reused_variant_id,
            variant_id,
            "When creating a variant with the same data we should get the same variant",
        )

    def test_custom(self):
        ProductTemplate = self.env["product.template"]

        vals = self.variant_creation_vals.copy()
        vals.update(
            {
                "cpq_ok": True,
            }
        )
        product_tmpl_id = ProductTemplate.create(vals)

        ptav_ids = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_attribute_value_id", "=", self.prod_attrib_colour_custom.id),
            ],
            limit=1,
        )

        # generate a random name
        cow_print = "COW PRINT %s" % (uuid.uuid4())

        custom_dict = {ptav_ids: cow_print}

        variant_id = product_tmpl_id._cpq_get_create_variant(
            ptav_ids,
            custom_dict,
        )
        self.assertEqual(variant_id.product_template_attribute_value_ids, ptav_ids)
        self.assertEqual(
            len(variant_id.cpq_custom_value_ids),
            1,
            "There should only be 1 custom value",
        )
        self.assertEqual(variant_id.cpq_custom_value_ids.custom_value, cow_print)

        self.assertTrue(
            cow_print in variant_id.display_name,
            "Expected the custom value in the variant display name",
        )
