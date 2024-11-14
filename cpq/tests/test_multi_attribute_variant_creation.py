import random

from odoo.exceptions import UserError

from odoo.addons.cpq.tests.common import TestCpqCommon

COW_PRINT = "Cow Print"


class TestMultiAttributeVariantCreation(TestCpqCommon):
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
                ),
                (
                    0,
                    0,
                    {
                        "attribute_id": self.prod_attrib_size.id,
                        "value_ids": [
                            (
                                6,
                                0,
                                [
                                    self.prod_attrib_size_small.id,
                                    self.prod_attrib_size_medium.id,
                                    self.prod_attrib_size_large.id,
                                    self.prod_attrib_size_custom.id,
                                ],
                            )
                        ],
                    },
                ),
            ],
        }

    def test_cpq_variant_creation_fails_without_all_attribs(self):
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

        with self.assertRaises(UserError):
            product_tmpl_id._cpq_get_create_variant(
                ptav_ids,
                None,
            )

    def test_cpq_variant_reuse(self):
        ProductTemplate = self.env["product.template"]

        vals = self.variant_creation_vals.copy()
        vals.update(
            {
                "cpq_ok": True,
            }
        )
        product_tmpl_id = ProductTemplate.create(vals)

        ptav_red_id = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_attribute_value_id", "=", self.prod_attrib_colour_red.id),
            ],
            limit=1,
        )

        ptav_small_id = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_attribute_value_id", "=", self.prod_attrib_size_small.id),
            ],
            limit=1,
        )

        ptav_ids = ptav_small_id | ptav_red_id

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

        ptav_red_id = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_attribute_value_id", "=", self.prod_attrib_colour_red.id),
            ],
            limit=1,
        )

        ptav_custom_id = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_attribute_value_id", "=", self.prod_attrib_size_custom.id),
            ],
            limit=1,
        )

        ptav_ids = ptav_custom_id | ptav_red_id

        # generate a random name
        size = random.randint(1, 99)

        custom_dict = {ptav_custom_id: size}

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
        self.assertEqual(variant_id.cpq_custom_value_ids.custom_value, str(size))

        self.assertTrue(
            str(size) in variant_id.display_name,
            "Expected the custom value in the variant display name",
        )

    def test_no_propagate(self):
        ProductTemplate = self.env["product.template"]

        self.prod_attrib_size.cpq_propagate_to_variant = False

        vals = self.variant_creation_vals.copy()
        vals.update(
            {
                "cpq_ok": True,
            }
        )
        product_tmpl_id = ProductTemplate.create(vals)

        ptav_red_id = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_attribute_value_id", "=", self.prod_attrib_colour_red.id),
            ],
            limit=1,
        )

        ptav_custom_id = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_attribute_value_id", "=", self.prod_attrib_size_custom.id),
            ],
            limit=1,
        )

        ptav_ids = ptav_custom_id | ptav_red_id

        # generate a random name
        size = random.randint(1, 99)

        custom_dict = {ptav_custom_id: size}

        variant_id = product_tmpl_id._cpq_get_create_variant(
            ptav_ids,
            custom_dict,
        )
        self.assertEqual(variant_id.product_template_attribute_value_ids, ptav_red_id)
        self.assertEqual(
            len(variant_id.cpq_custom_value_ids),
            0,
            "There should only be 0 custom values",
        )
