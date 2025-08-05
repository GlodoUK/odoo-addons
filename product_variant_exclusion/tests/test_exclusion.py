from odoo import Command
from odoo.tests import TransactionCase


class TestExclusion(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.size_attribute = cls.env["product.attribute"].create(
            {
                "name": "Size",
                "value_ids": [
                    Command.create({"name": "S"}),
                    Command.create({"name": "M"}),
                    Command.create({"name": "L"}),
                ],
            }
        )
        (
            cls.size_attribute_s,
            cls.size_attribute_m,
            cls.size_attribute_l,
        ) = cls.size_attribute.value_ids

        cls.colour_attribute = cls.env["product.attribute"].create(
            {
                "name": "Colour",
                "value_ids": [
                    Command.create({"name": "red", "sequence": 1}),
                    Command.create({"name": "blue", "sequence": 2}),
                    Command.create({"name": "green", "sequence": 3}),
                ],
            }
        )
        (
            cls.color_attribute_red,
            cls.color_attribute_blue,
            cls.color_attribute_green,
        ) = cls.colour_attribute.value_ids

        cls.thing_attribute = cls.env["product.attribute"].create(
            {
                "name": "Thing",
                "value_ids": [
                    Command.create({"name": "1", "sequence": 1}),
                    Command.create({"name": "2", "sequence": 2}),
                    Command.create({"name": "3", "sequence": 3}),
                ],
            }
        )
        (
            cls.thing_attribute_1,
            cls.thing_attribute_2,
            cls.thing_attribute_3,
        ) = cls.thing_attribute.value_ids

        cls.shirt = cls.env["product.template"].create(
            {
                "name": "Shirt",
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": cls.size_attribute.id,
                            "value_ids": [
                                Command.set(cls.size_attribute.value_ids.ids)
                            ],
                        }
                    ),
                    Command.create(
                        {
                            "attribute_id": cls.colour_attribute.id,
                            "value_ids": [
                                Command.set(cls.colour_attribute.value_ids.ids)
                            ],
                        }
                    ),
                    Command.create(
                        {
                            "attribute_id": cls.thing_attribute.id,
                            "value_ids": [
                                Command.set(cls.thing_attribute.value_ids.ids)
                            ],
                        }
                    ),
                ],
            }
        )

    def test_no_exclusion(self):
        self.assertEqual(self.shirt.product_variant_count, 27)

    def test_full_exclusion(self):
        ptav_ids = self.env["product.template.attribute.value"]

        for exclude in [
            self.size_attribute_l,
            self.color_attribute_blue,
            self.thing_attribute_1,
        ]:
            ptav_ids |= self.env["product.template.attribute.value"].search(
                [
                    ("product_attribute_value_id", "=", exclude.id),
                    ("product_tmpl_id", "=", self.shirt.id),
                ]
            )

        self.assertEqual(len(ptav_ids), 3)

        self.assertTrue(self.shirt._is_combination_possible(ptav_ids))

        excl_ids = self.env["product.variant.exclusion"].create(
            {"tmpl_id": self.shirt.id, "ptav_ids": [Command.set(ptav_ids.ids)]}
        )
        self.assertEqual(self.shirt.product_variant_count, 26)

        self.assertFalse(self.shirt._is_combination_possible(ptav_ids))

        excl_ids.unlink()
        self.assertEqual(self.shirt.product_variant_count, 27)

    def test_partial_exclusion(self):
        ptav_exclude_id = self.env["product.template.attribute.value"].search(
            [
                ("product_attribute_value_id", "=", self.color_attribute_blue.id),
                ("product_tmpl_id", "=", self.shirt.id),
            ]
        )

        invalid_combination = self.env["product.template.attribute.value"].search(
            [
                (
                    "product_attribute_value_id",
                    "in",
                    [
                        self.color_attribute_blue.id,
                        self.size_attribute_l.id,
                        self.thing_attribute_1.id,
                    ],
                ),
                ("product_tmpl_id", "=", self.shirt.id),
            ]
        )

        self.assertTrue(self.shirt._is_combination_possible(invalid_combination))

        excl_ids = self.env["product.variant.exclusion"].create(
            {"tmpl_id": self.shirt.id, "ptav_ids": [Command.set(ptav_exclude_id.ids)]}
        )
        self.assertEqual(self.shirt.product_variant_count, 18)

        self.assertFalse(self.shirt._is_combination_possible(invalid_combination))

        excl_ids.unlink()
        self.assertEqual(self.shirt.product_variant_count, 27)
