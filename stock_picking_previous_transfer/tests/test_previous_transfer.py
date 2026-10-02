from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPreviousTransfer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].create(
            {"name": "PT Warehouse", "code": "PTW", "delivery_steps": "pick_pack_ship"}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "PT Widget", "default_code": "PT-WIDGET-1", "is_storable": True}
        )
        wh = cls.warehouse
        customers = cls.env.ref("stock.stock_location_customers")
        cls.pick, cls.pack, cls.ship = (
            cls._picking(picking_type, source, dest)
            for picking_type, source, dest in (
                (wh.pick_type_id, wh.lot_stock_id, wh.wh_pack_stock_loc_id),
                (wh.pack_type_id, wh.wh_pack_stock_loc_id, wh.wh_output_stock_loc_id),
                (wh.out_type_id, wh.wh_output_stock_loc_id, customers),
            )
        )
        cls.pick.move_ids.move_dest_ids = cls.pack.move_ids
        cls.pack.move_ids.move_dest_ids = cls.ship.move_ids

    @classmethod
    def _picking(cls, picking_type, source, dest):
        return cls.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": source.id,
                "location_dest_id": dest.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 1,
                            "location_id": source.id,
                            "location_dest_id": dest.id,
                        },
                    )
                ],
            }
        )

    def test_walks_the_chain_backwards(self):
        self.assertEqual(self.ship._get_previous_transfers(), self.pack)
        self.assertEqual(self.pack._get_previous_transfers(), self.pick)
        self.assertFalse(self.pick.show_previous_pickings)
        action = self.ship.action_previous_transfer()
        self.assertEqual(action["res_id"], self.pack.id)

    def test_the_transfer_returned_is_not_previous(self):
        self.ship.return_id = self.pack
        self.assertFalse(self.ship._get_previous_transfers())
