from odoo.tests.common import TransactionCase


class TestPreReserveCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_stock_multi_locations = cls.env.ref("stock.group_stock_multi_locations")
        cls.env.user.write({"groups_id": [(4, group_stock_multi_locations.id, 0)]})
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )

        cls.customer_move1 = cls.env["stock.move"].create(
            {
                "name": "test_in_1",
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "product_id": cls.product.id,
                "product_uom": cls.uom_unit.id,
                "product_uom_qty": 75.0,
                "date": "2019-01-01",
            }
        )
        cls.customer_move2 = cls.env["stock.move"].create(
            {
                "name": "test_in_1",
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "product_id": cls.product.id,
                "product_uom": cls.uom_unit.id,
                "product_uom_qty": 50.0,
                "date": "2022-01-01",
            }
        )
        cls.receipt_move = cls.env["stock.move"].create(
            {
                "name": "test_in_1",
                "location_id": cls.supplier_location.id,
                "location_dest_id": cls.stock_location.id,
                "product_id": cls.product.id,
                "product_uom": cls.uom_unit.id,
                "product_uom_qty": 100.0,
            }
        )
