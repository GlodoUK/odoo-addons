from odoo.tests import tagged

from odoo.addons.product_commingle.tests.common import CommonCommingleCase


@tagged("post_install", "-at_install")
class TestMrp(CommonCommingleCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_bolta.type = "product"
        cls.product_boltb.type = "product"
        cls.product_bolt_equiv.type = "product"
        cls.product_bolt_equiv.commingled_policy = "strict"

        cls.partner_id = cls.env["res.partner"].create({"name": "Partner A"})
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

        cls.product_bolt_kit = cls.env["product.product"].create(
            {
                "name": "Bolt Kit",
                "type": "product",
            }
        )

        cls.bom_equiv_kit = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product_bolt_kit.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "phantom",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_bolt_equiv.id,
                            "product_qty": 1.0,
                            "product_uom_id": cls.product_bolt_equiv.uom_id.id,
                        },
                    ),
                ],
            }
        )

    def test_simple_stock_move_nested_inside_kit(self):
        picking_id = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_bolt_kit.id,
                            "product_uom": self.product_bolt_kit.uom_id.id,
                            "product_uom_qty": 1.0,
                            "name": "test_move_1",
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                            "picking_type_id": self.env.ref(
                                "stock.picking_type_out"
                            ).id,
                        },
                    ),
                ],
            }
        )

        picking_id.action_confirm()
        self.assertEqual(len(picking_id.move_lines), 1)
        self.assertEqual(picking_id.move_lines.product_id, self.product_bolta)
