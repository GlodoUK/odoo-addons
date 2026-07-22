from odoo.tests.common import TransactionCase

from odoo.addons.pipeline.tools import batch


class TestBatchTools(TransactionCase):
    def test_batches_with_short_final_chunk(self):
        self.assertEqual(list(batch.batched(range(5), 2)), [[0, 1], [2, 3], [4]])

    def test_exact_multiple(self):
        self.assertEqual(list(batch.batched(range(4), 2)), [[0, 1], [2, 3]])

    def test_size_larger_than_input_is_one_chunk(self):
        self.assertEqual(list(batch.batched([1, 2], 10)), [[1, 2]])

    def test_empty_iterable_yields_nothing(self):
        self.assertEqual(list(batch.batched([], 3)), [])

    def test_yields_lists(self):
        self.assertIsInstance(next(batch.batched([1, 2, 3], 2)), list)

    def test_size_below_one_raises(self):
        with self.assertRaises(ValueError):
            list(batch.batched([1, 2], 0))
