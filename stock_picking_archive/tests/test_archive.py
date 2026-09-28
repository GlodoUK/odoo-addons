from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestArchive(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Definitely Not a Pedal Bin",
                "type": "consu",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.stock_picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.picking_type_out.id,
                "location_id": cls.picking_type_out.default_location_src_id.id,
                "location_dest_id": cls.picking_type_out.default_location_dest_id.id,
            }
        )
        cls.env["stock.move"].create(
            {
                "product_id": cls.product.id,
                "product_uom_qty": 10,
                "product_uom": cls.product.uom_id.id,
                "picking_id": cls.stock_picking.id,
                "location_id": cls.picking_type_out.default_location_src_id.id,
                "location_dest_id": cls.picking_type_out.default_location_dest_id.id,
            }
        )

    def test_stock_picking_archive_toggle_active(self):
        self.assertTrue(self.stock_picking.active)
        self.stock_picking.action_archive()
        self.assertFalse(self.stock_picking.active)
        self.stock_picking.action_unarchive()
        self.assertTrue(self.stock_picking.active)

    def test_stock_picking_archive_toggle_active_locked(self):
        self.assertTrue(self.stock_picking.active)
        self.stock_picking.state = "confirmed"
        with self.assertRaises(UserError):
            self.stock_picking.action_archive()

    def test_stock_picking_archive_cancelled_toggle_active(self):
        self.assertTrue(self.stock_picking.active)
        self.stock_picking.action_cancel()
        self.stock_picking.action_archive()
        self.assertFalse(self.stock_picking.active)
