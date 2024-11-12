from .common import TestPreReserveCommon


class TestPreReserve(TestPreReserveCommon):
    def test_no_preserve(self):
        self.customer_move1._action_confirm()
        self.customer_move2._action_confirm()
        self.receipt_move._action_confirm()

        move_line = self.receipt_move.move_line_ids[0]
        self.assertEqual(move_line.product_qty, 100.0)
        self.assertEqual(move_line.qty_done, 0.0)
        move_line.qty_done = 100.0

        self.receipt_move._action_done()

        self.assertEqual(self.customer_move1.reserved_availability, 0.0)
        self.assertEqual(self.customer_move2.reserved_availability, 0.0)

        (self.customer_move1 + self.customer_move2)._action_assign()

        self.assertEqual(self.customer_move1.reserved_availability, 75.0)
        self.assertEqual(self.customer_move2.reserved_availability, 25.0)

    def test_preserve(self):
        self.customer_move1._action_confirm()
        self.customer_move2._action_confirm()

        self.assertEqual(self.receipt_move.prereserved_qty, 0.0)
        self.assertEqual(self.receipt_move.prereserved_available_qty, 0.0)

        self.receipt_move._action_confirm()

        self.assertEqual(self.receipt_move.prereserved_qty, 0.0)
        self.assertEqual(
            self.receipt_move.prereserved_available_qty,
            self.receipt_move.product_uom_qty,
        )

        self.env["stock.move.prereserved"]._link_moves(
            self.receipt_move,
            self.customer_move2,
        )

        move_line = self.receipt_move.move_line_ids[0]
        self.assertEqual(move_line.product_qty, 100.0)
        self.assertEqual(move_line.qty_done, 0.0)
        move_line.qty_done = 100.0

        self.receipt_move._action_done()

        self.assertEqual(self.customer_move1.reserved_availability, 0.0)
        self.assertEqual(self.customer_move2.reserved_availability, 50.0)

        (self.customer_move1 + self.customer_move2)._action_assign()

        self.assertEqual(self.customer_move1.reserved_availability, 50.0)
        self.assertEqual(self.customer_move2.reserved_availability, 50.0)

    def test_unlink_preserve(self):
        self.customer_move1._action_confirm()
        self.customer_move2._action_confirm()
        self.receipt_move._action_confirm()

        self.env["stock.move.prereserved"]._link_moves(
            self.receipt_move,
            self.customer_move2,
        )

        self.assertTrue(self.customer_move2 in self.receipt_move.move_dest_ids)

        self.env["stock.move.prereserved"]._unlink_orig_moves(self.customer_move2)

        self.assertEqual(self.receipt_move.prereserved_qty, 0.0)
        self.assertEqual(
            self.receipt_move.prereserved_available_qty,
            self.receipt_move.product_uom_qty,
        )

        self.assertTrue(self.customer_move2 not in self.receipt_move.move_dest_ids)

    def test_candidates(self):
        self.customer_move1._action_confirm()
        self.customer_move2._action_confirm()
        self.receipt_move.write({"product_uom_qty": 50.0})
        self.receipt_move._action_confirm()

        self.assertTrue(
            self.receipt_move in self.customer_move1._get_candidate_future_moves()
        )

        self.assertTrue(
            self.receipt_move in self.customer_move1._get_candidate_future_moves()
        )

        self.env["stock.move.prereserved"]._link_moves(
            self.receipt_move,
            self.customer_move2,
        )
