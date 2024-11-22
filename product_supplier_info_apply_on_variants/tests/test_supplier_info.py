from odoo.fields import Command
from odoo.tests import TransactionCase, tagged
from odoo.tools import float_compare


@tagged("post_install", "-at_install")
class TestSupplierInfo(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wood_corner = cls.env["res.partner"].create({"name": "Wood Corner"})
        cls.azure_int = cls.env["res.partner"].create({"name": "Azure Interior"})

    def test_default_select_seller(self):
        self.ipad_mini, self.monitor = self.env["product.product"].create(
            [
                {
                    "name": "Large Cabinet",
                    "standard_price": 800.0,
                },
                {
                    "name": "Super nice monitor",
                    "list_price": 1000.0,
                },
            ]
        )

        self.env["product.supplierinfo"].create(
            [
                {
                    "name": self.wood_corner.id,
                    "product_tmpl_id": self.ipad_mini.product_tmpl_id.id,
                    "delay": 3,
                    "min_qty": 1,
                    "price": 750,
                },
                {
                    "name": self.azure_int.id,
                    "product_tmpl_id": self.ipad_mini.product_tmpl_id.id,
                    "delay": 3,
                    "min_qty": 1,
                    "price": 790,
                },
                {
                    "name": self.azure_int.id,
                    "product_tmpl_id": self.ipad_mini.product_tmpl_id.id,
                    "delay": 3,
                    "min_qty": 3,
                    "price": 785,
                },
                {
                    "name": self.azure_int.id,
                    "product_tmpl_id": self.monitor.product_tmpl_id.id,
                    "delay": 3,
                    "min_qty": 3,
                    "price": 100,
                },
            ]
        )

        product = self.ipad_mini

        # Supplierinfo pricing

        # Check cost price of ipad mini
        price = product._select_seller(partner_id=self.azure_int, quantity=1.0).price
        self.assertEqual(float_compare(price, 790, precision_digits=2), 0)

        # Check cost price of ipad mini if more than 3 Unit
        price = product._select_seller(partner_id=self.azure_int, quantity=3.0).price
        self.assertEqual(float_compare(price, 785, precision_digits=2), 0)

    def test_apply_on_variants(self):
        attrib_memory = self.env["product.attribute"].create(
            {
                "name": "Storage",
                "sequence": 1,
                "value_ids": [
                    Command.create(
                        {
                            "name": "256 GB",
                            "sequence": 1,
                        }
                    ),
                    Command.create(
                        {
                            "name": "512 GB",
                            "sequence": 2,
                        }
                    ),
                ],
            }
        )

        attrib_value_256, attrib_value_512 = attrib_memory.value_ids

        thingy = self.env["product.template"].create(
            {
                "name": "Thingy with memory",
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": attrib_memory.id,
                            "value_ids": [
                                Command.set([attrib_value_256.id, attrib_value_512.id])
                            ],
                        }
                    )
                ],
            }
        )

        thingy_256, thingy_512 = thingy.product_variant_ids

        self.env["product.supplierinfo"].create(
            [
                {
                    "sequence": 1,
                    "name": self.azure_int.id,
                    "product_tmpl_id": thingy.id,
                    "delay": 3,
                    "min_qty": 99,
                    "price": 1,
                },
                {
                    "sequence": 2,
                    "name": self.azure_int.id,
                    "product_tmpl_id": thingy.id,
                    "delay": 3,
                    "min_qty": 1,
                    "price": 2,
                    "apply_on_ptav_ids": [
                        Command.set(thingy_512.product_template_attribute_value_ids.ids)
                    ],
                },
                {
                    "sequence": 3,
                    "name": self.azure_int.id,
                    "product_tmpl_id": thingy.id,
                    "delay": 3,
                    "min_qty": 1,
                    "price": 3,
                    "apply_on_ptav_ids": [
                        Command.set(thingy_256.product_template_attribute_value_ids.ids)
                    ],
                },
            ]
        )

        # price for 99+ is always 790

        price = thingy_256._select_seller(
            partner_id=self.azure_int, quantity=99.0
        ).price
        self.assertEqual(
            float_compare(price, 1, precision_digits=2), 0, f"{price} != 1"
        )

        price = thingy_512._select_seller(
            partner_id=self.azure_int, quantity=99.0
        ).price
        self.assertEqual(
            float_compare(price, 1, precision_digits=2), 0, f"{price} != 1"
        )

        # now test apply on variants

        price = thingy_256._select_seller(partner_id=self.azure_int, quantity=1.0).price
        self.assertEqual(
            float_compare(price, 3, precision_digits=2), 0, f"{price} != 3"
        )

        price = thingy_512._select_seller(partner_id=self.azure_int, quantity=1.0).price
        self.assertEqual(
            float_compare(price, 2, precision_digits=2), 0, f"{price} != 2"
        )
