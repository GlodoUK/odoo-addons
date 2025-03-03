from odoo.addons.product_meta.tests.common import TestMetaCommon


class TestStockMove(TestMetaCommon):
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

    def test_stock_picking(self):
        sale_id = self.sale_id
        sale_id.action_confirm()

        self.assertTrue(sale_id.picking_ids.has_meta_lines)

        for sale_line_id in sale_id.order_line.filtered(
            lambda line: line.meta_parent_line_id
        ):
            self.assertTrue(
                sale_line_id.meta_tmpl_line_id.parent_id,
                sale_line_id.move_ids.product_tmpl_meta_line_parent_id,
            )
