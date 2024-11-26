from random import randint

from odoo.addons.cpq.tests.common import TestCpqCommon


class TestNormalBom(TestCpqCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_bolt = cls.env["product.product"].create(
            {"type": "product", "name": "Bolt"}
        )

        cls.product_washer = cls.env["product.product"].create(
            {"type": "product", "name": "Bolt"}
        )

        cls.product_tmpl_chair_fabric_no_cpq = cls.env["product.template"].create(
            {
                "type": "product",
                "name": "Chair Fabric",
                "cpq_ok": False,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.prod_attrib_colour.id,
                            "value_ids": [
                                (
                                    6,
                                    0,
                                    [
                                        cls.prod_attrib_colour_red.id,
                                        cls.prod_attrib_colour_blue.id,
                                        cls.prod_attrib_colour_green.id,
                                    ],
                                )
                            ],
                        },
                    ),
                ],
            }
        )

        cls.product_tmpl_chair_base_cpq = cls.env["product.template"].create(
            {
                "type": "product",
                "name": "Chair Base",
                "cpq_ok": True,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.prod_attrib_size.id,
                            "value_ids": [
                                (
                                    6,
                                    0,
                                    [
                                        cls.prod_attrib_size_small.id,
                                        cls.prod_attrib_size_medium.id,
                                        cls.prod_attrib_size_large.id,
                                        cls.prod_attrib_size_custom.id,
                                    ],
                                )
                            ],
                        },
                    ),
                ],
            }
        )

        cls.product_tmpl_chair_cpq = cls.env["product.template"].create(
            {
                "type": "product",
                "name": "Built Chair",
                "cpq_ok": True,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.prod_attrib_colour.id,
                            "value_ids": [
                                (
                                    6,
                                    0,
                                    [
                                        cls.prod_attrib_colour_red.id,
                                        cls.prod_attrib_colour_blue.id,
                                        cls.prod_attrib_colour_green.id,
                                        cls.prod_attrib_colour_custom.id,
                                    ],
                                )
                            ],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.prod_attrib_size.id,
                            "value_ids": [
                                (
                                    6,
                                    0,
                                    [
                                        cls.prod_attrib_size_small.id,
                                        cls.prod_attrib_size_medium.id,
                                        cls.prod_attrib_size_large.id,
                                        cls.prod_attrib_size_custom.id,
                                    ],
                                )
                            ],
                        },
                    ),
                ],
            }
        )

    def assertBoMExplosionEqual(self, parts, expected):
        self.assertEqual(len(parts), len(expected))

        for found, expected in zip(parts, expected):  # noqa: B020
            (found_product_id, found_quantity, found_uom, _found_cpq_bom_line) = found
            (
                expected_product_id,
                expected_quantity,
                expected_uom,
                _expected_cpq_bom_line,
            ) = expected

            self.assertEqual(
                found_product_id,
                expected_product_id,
                "Found: {p_id} ({d_name}), Expected {ep_id} ({e_dname}))".format(
                    p_id=found_product_id,
                    d_name=found_product_id.display_name,
                    ep_id=expected_product_id,
                    e_dname=expected_product_id.display_name,
                ),
            )
            self.assertEqual(found_quantity, expected_quantity)
            self.assertEqual(found_uom, expected_uom)

    def test_explosion(self):
        # create a bom with:
        #  - 4x bolts (variant)
        #  - 4x washers (variant)
        #  - 1x Chair Fabric (template - which is not configurable - expectation
        #                     is that attributes will passthru)
        #  - 1x Chair Base (template - configurable, attribute passthru)
        #  - No Custom options

        bom_id = self.env["cpq.dynamic.bom"].create(
            {
                "type": "normal",
                "product_tmpl_id": self.product_tmpl_chair_cpq.id,
                "product_uom_id": self.product_tmpl_chair_cpq.uom_id.id,
                "product_qty": 1,
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "component_type": "variant",
                            "component_product_id": self.product_bolt.id,
                            "quantity_type": "fixed",
                            "quantity_fixed": 4.0,
                            "condition_type": "always",
                            "uom_id": self.product_bolt.uom_id.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "component_type": "variant",
                            "component_product_id": self.product_washer.id,
                            "quantity_type": "fixed",
                            "quantity_fixed": 4.0,
                            "condition_type": "always",
                            "uom_id": self.product_washer.uom_id.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "component_type": "template",
                            "component_product_tmpl_id": self.product_tmpl_chair_fabric_no_cpq.id,  # noqa: B950, E501
                            "quantity_type": "fixed",
                            "quantity_fixed": 1.0,
                            "condition_type": "always",
                            "uom_id": self.product_tmpl_chair_fabric_no_cpq.uom_id.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "component_type": "template",
                            "component_product_tmpl_id": (
                                self.product_tmpl_chair_base_cpq.id
                            ),
                            "quantity_type": "fixed",
                            "quantity_fixed": 1.0,
                            "condition_type": "always",
                            "uom_id": self.product_tmpl_chair_base_cpq.uom_id.id,
                        },
                    ),
                ],
            }
        )

        # lets build a small red chair

        ptav_red_id = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", self.product_tmpl_chair_cpq.id),
                ("product_attribute_value_id", "=", self.prod_attrib_colour_red.id),
            ],
            limit=1,
        )

        ptav_small_id = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", self.product_tmpl_chair_cpq.id),
                ("product_attribute_value_id", "=", self.prod_attrib_size_small.id),
            ],
            limit=1,
        )

        variant_id = self.product_tmpl_chair_cpq._cpq_get_create_variant(
            ptav_small_id | ptav_red_id,
            None,
        )

        # ensure that we explode *first* as we may be creating some
        # product.product
        exploded = bom_id.explode(variant_id, 1.0)

        product_red_fabric = (
            self.env["product.template.attribute.value"]
            .search(
                [
                    ("product_attribute_value_id", "=", self.prod_attrib_colour_red.id),
                    ("product_tmpl_id", "=", self.product_tmpl_chair_fabric_no_cpq.id),
                ],
                limit=1,
            )
            .ptav_product_variant_ids
        )

        product_small_chair_base = (
            self.env["product.template.attribute.value"]
            .search(
                [
                    ("product_attribute_value_id", "=", self.prod_attrib_size_small.id),
                    ("product_tmpl_id", "=", self.product_tmpl_chair_base_cpq.id),
                ],
                limit=1,
            )
            .ptav_product_variant_ids
        )

        self.assertBoMExplosionEqual(
            exploded,
            [
                (self.product_bolt, 4.0, self.product_bolt.uom_id, None),
                (self.product_washer, 4.0, self.product_washer.uom_id, None),
                (product_red_fabric, 1.0, product_red_fabric.uom_id, None),
                (product_small_chair_base, 1.0, product_small_chair_base.uom_id, None),
            ],
        )

    def test_custom_explosion(self):
        # create a bom with:
        #  - 4x bolts (variant)
        #  - 4x washers (variant)
        #  - 1x Chair Fabric (template - which is not configurable - expectation
        #                     is that attributes will passthru)
        #  - 1x Chair Base (template - configurable, attribute passthru)
        # Custom value

        bom_id = self.env["cpq.dynamic.bom"].create(
            {
                "type": "normal",
                "product_tmpl_id": self.product_tmpl_chair_cpq.id,
                "product_uom_id": self.product_tmpl_chair_cpq.uom_id.id,
                "product_qty": 1,
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "component_type": "variant",
                            "component_product_id": self.product_bolt.id,
                            "quantity_type": "fixed",
                            "quantity_fixed": 4.0,
                            "condition_type": "always",
                            "uom_id": self.product_bolt.uom_id.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "component_type": "variant",
                            "component_product_id": self.product_washer.id,
                            "quantity_type": "fixed",
                            "quantity_fixed": 4.0,
                            "condition_type": "always",
                            "uom_id": self.product_washer.uom_id.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "component_type": "template",
                            "component_product_tmpl_id": self.product_tmpl_chair_fabric_no_cpq.id,  # noqa: B950, E501
                            "quantity_type": "fixed",
                            "quantity_fixed": 1.0,
                            "condition_type": "always",
                            "uom_id": self.product_tmpl_chair_fabric_no_cpq.uom_id.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "component_type": "template",
                            "component_product_tmpl_id": (
                                self.product_tmpl_chair_base_cpq.id
                            ),
                            "quantity_type": "fixed",
                            "quantity_fixed": 1.0,
                            "condition_type": "always",
                            "uom_id": self.product_tmpl_chair_base_cpq.uom_id.id,
                        },
                    ),
                ],
            }
        )

        # lets build a small red chair

        ptav_red_id = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", self.product_tmpl_chair_cpq.id),
                ("product_attribute_value_id", "=", self.prod_attrib_colour_red.id),
            ],
            limit=1,
        )

        ptav_custom_id = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", self.product_tmpl_chair_cpq.id),
                ("product_attribute_value_id", "=", self.prod_attrib_size_custom.id),
            ],
            limit=1,
        )

        custom_size = randint(1, 99)

        variant_id = self.product_tmpl_chair_cpq._cpq_get_create_variant(
            ptav_red_id | ptav_custom_id, {ptav_custom_id: custom_size}
        )

        # ensure that we explode *first* as we may be creating some
        # product.product
        exploded = bom_id.explode(variant_id, 1.0)

        product_red_fabric = (
            self.env["product.template.attribute.value"]
            .search(
                [
                    ("product_attribute_value_id", "=", self.prod_attrib_colour_red.id),
                    ("product_tmpl_id", "=", self.product_tmpl_chair_fabric_no_cpq.id),
                ],
                limit=1,
            )
            .ptav_product_variant_ids
        )

        product_small_chair_custom = (
            self.env["product.template.attribute.value"]
            .search(
                [
                    (
                        "product_attribute_value_id",
                        "=",
                        self.prod_attrib_size_custom.id,
                    ),
                    ("product_tmpl_id", "=", self.product_tmpl_chair_base_cpq.id),
                ],
                limit=1,
            )
            .ptav_product_variant_ids
        )

        self.assertEqual(
            product_small_chair_custom.cpq_custom_value_ids.custom_value,
            str(custom_size),
        )

        self.assertBoMExplosionEqual(
            exploded,
            [
                (self.product_bolt, 4.0, self.product_bolt.uom_id, None),
                (self.product_washer, 4.0, self.product_washer.uom_id, None),
                (product_red_fabric, 1.0, product_red_fabric.uom_id, None),
                (
                    product_small_chair_custom,
                    1.0,
                    product_small_chair_custom.uom_id,
                    None,
                ),
            ],
        )
