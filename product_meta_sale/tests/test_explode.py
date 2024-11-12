from odoo.addons.product_meta.tests.common import TestMetaCommon


class TestExplode(TestMetaCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.sale_partner = cls.env["res.partner"].create(
            {
                "name": "Sale Partner A",
            }
        )

        cls.sale_id = cls.env["sale.order"].create(
            {
                "partner_id": cls.sale_partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_meta_1.product_variant_ids.id,
                        },
                    )
                ],
            }
        )

    def test_explosion(self):
        sale_id = self.sale_id

        self.assertEqual(len(sale_id.order_line), 3)

        self.assertEqual(
            sale_id.order_line[0].product_id, self.product_meta_1.product_variant_ids[0]
        )

        self.assertEqual(
            sale_id.order_line[0].meta_child_line_ids,
            sale_id.order_line[1:],
        )

        i = 0

        for meta_line_id in self.product_meta_1.meta_product_tmpl_line_ids:
            i += 1
            line_id = sale_id.order_line[i]

            self.assertEqual(
                line_id.product_id,
                meta_line_id.child_variant_id,
            )

            self.assertEqual(
                line_id.product_uom_qty,
                meta_line_id.quantity,
            )

    def test_quantity_change(self):
        sale_id = self.sale_id

        sale_id.order_line[0].write({"product_uom_qty": 2.0})

        i = 0

        for meta_line_id in self.product_meta_1.meta_product_tmpl_line_ids:
            i += 1
            line_id = sale_id.order_line[i]

            self.assertEqual(
                line_id.product_id,
                meta_line_id.child_variant_id,
            )

            self.assertEqual(
                line_id.product_uom_qty,
                meta_line_id.quantity * 2.0,
            )

    def test_resequence(self):
        sale_id = self.sale_id

        sale_id.order_line[0].write({"sequence": 5})

        self.assertTrue(all(line.sequence == 5 for line in sale_id.order_line))
