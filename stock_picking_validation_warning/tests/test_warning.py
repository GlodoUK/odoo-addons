from odoo.tests.common import TransactionCase


class TestWarning(TransactionCase):
    def setUp(self):
        super().setUp()

        self.warehouse = self.env.ref("stock.warehouse0")
        self.picking_type_out = self.warehouse.out_type_id
        self.product = self.env["product.product"].create(
            {
                "type": "product",
                "name": "Test Product",
            }
        )

        self.parent = self.env["res.partner"].create(
            {
                "name": "Customer with a warn",
                "email": "customer@example.com",
                "picking_warn": "warning",
                "picking_warn_msg": "parent warning!",
            }
        )
        self.warn_msg = "This customer has a warn"
        self.partner = self.env["res.partner"].create(
            {
                "name": "Customer with a warn",
                "email": "customer@example.com",
                "picking_warn": "warning",
                "picking_warn_msg": "customer warning!",
            }
        )
        self.location = self.env["stock.location"].create(
            {
                "name": "Test Location",
                "usage": "internal",
                "location_id": self.warehouse.view_location_id.id,
            }
        )
        self.customer_location = self.env["stock.location"].create(
            {
                "name": "Customer Location",
                "usage": "internal",
                "location_id": self.warehouse.view_location_id.id,
            }
        )

    def test_compute_picking_warn_msg(self):
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.location.id,
                "location_dest_id": self.customer_location.id,
                "move_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_id": self.product.uom_id.id,
                            "quantity_product_uom": 1,
                            "location_dest_id": self.customer_location.id,
                            "location_id": self.location.id,
                        },
                    ),
                ],
            }
        )

        res = picking.button_validate()
        self.assertEqual(res.get("res_model"), "stock.picking.warning")
        warning_id = self.env["stock.picking.warning"].browse(res.get("res_id"))
        self.assertEqual(warning_id.msg, picking.partner_id.picking_warn_msg)

    def test_compute_picking_warn_msg_parent(self):
        self.partner.write(
            {
                "parent_id": self.parent.id,
                "picking_warn": "no-message",
            }
        )

        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.location.id,
                "location_dest_id": self.customer_location.id,
                "move_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_id": self.product.uom_id.id,
                            "quantity_product_uom": 1,
                            "location_id": self.location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    ),
                ],
            }
        )

        res = picking.button_validate()
        self.assertEqual(res.get("res_model"), "stock.picking.warning")
        warning_id = self.env["stock.picking.warning"].browse(res.get("res_id"))
        self.assertEqual(warning_id.msg, self.parent.picking_warn_msg)
