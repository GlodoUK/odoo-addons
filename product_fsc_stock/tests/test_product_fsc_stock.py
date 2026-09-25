from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductFscStock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "FSC Board",
                "type": "consu",
                "fsc_certified": True,
                "fsc_classification": "fsc_100",
            }
        )

    def _create_picking(self, picking_type):
        return self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "location_id": picking_type.default_location_src_id.id,
                            "location_dest_id": (
                                picking_type.default_location_dest_id.id
                            ),
                        },
                    )
                ],
            }
        )

    def _render(self, picking):
        return (
            self.env["ir.actions.report"]
            ._render_qweb_html("stock.action_report_delivery", picking.ids)[0]
            .decode()
        )

    def test_move_snapshot(self):
        move = self._create_picking(self.env.ref("stock.picking_type_out")).move_ids
        self.assertEqual(move.fsc_label, "FSC 100%")
        self.product.fsc_classification = "fsc_recycled"
        self.assertEqual(move.fsc_label, "FSC 100%")

    def test_delivery_report(self):
        picking = self._create_picking(self.env.ref("stock.picking_type_out"))
        self.assertIn("FSC 100%", self._render(picking))

    def test_delivery_report_skips_cancelled(self):
        picking = self._create_picking(self.env.ref("stock.picking_type_out"))
        picking.move_ids._action_cancel()
        self.assertNotIn("FSC 100%", self._render(picking))

    def test_receipt_report_has_no_claims(self):
        picking = self._create_picking(self.env.ref("stock.picking_type_in"))
        self.assertNotIn("FSC 100%", self._render(picking))
