import datetime

from odoo.tests.common import TransactionCase


class TestAutomateLeadTime(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_id = self.env["res.partner"].create({"name": "Test Customer"})
        self.seller = self.env["res.partner"].create({"name": "Test Vendor"})
        self.product_id = self.env["product.template"].create(
            {
                "name": "Test Product",
                "sale_delay": 5,  # 5 Day Customer Lead Time
                "type": "consu",
                "is_storable": True,
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": self.seller.id,
                            "delay": 10,  # 10 Day Vendor Lead Time
                            "min_qty": 1,
                            "price": 100.0,
                        },
                    )
                ],
            }
        )

    def test_lead_time_default_method(self):
        self.product_id.sale_delay_method = "default"
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.product_variant_id.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        sale_line = sale_order.order_line[0]
        self.assertEqual(sale_line.customer_lead, 5)

    def test_lead_time_default_add_method(self):
        self.env.company.sale_lead_time_method = "add"
        self.product_id.sale_delay_method = "default"
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.product_variant_id.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        sale_line = sale_order.order_line[0]
        self.assertEqual(sale_line.customer_lead, 15)  # 5 + 10

    def test_lead_time_add_method(self):
        self.product_id.sale_delay_method = "add"
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.product_variant_id.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        sale_line = sale_order.order_line[0]
        self.assertEqual(sale_line.customer_lead, 15)  # 5 + 10

    def test_lead_time_replace_method(self):
        self.product_id.sale_delay_method = "replace"
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.product_variant_id.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        sale_line = sale_order.order_line[0]
        self.assertEqual(sale_line.customer_lead, 10)  # Vendor Lead Time only

    def test_lead_time_max_method(self):
        self.product_id.sale_delay_method = "max"
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.product_variant_id.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        sale_line = sale_order.order_line[0]
        self.assertEqual(sale_line.customer_lead, 10)  # Max of 5 and 10

    def test_lead_time_min_method(self):
        self.product_id.sale_delay_method = "min"
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.product_variant_id.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        sale_line = sale_order.order_line[0]
        self.assertEqual(sale_line.customer_lead, 5)  # Min of 5 and 10

    def test_product_in_stock_lead_time(self):
        self.product_id.sale_delay_method = "add"
        self.env["stock.quant"].create(
            {
                "product_id": self.product_id.product_variant_id.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "quantity": 100,  # Sufficient stock available
            }
        )
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.product_variant_id.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        sale_line = sale_order.order_line[0]
        self.assertEqual(sale_line.customer_lead, 5)  # Customer lead time only

    def test_reserved_stock_lead_time(self):
        self.product_id.sale_delay_method = "add"
        self.env["stock.quant"].create(
            {
                "product_id": self.product_id.product_variant_id.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "quantity": 1,  # Only 1 in stock
            }
        )
        sale_order_1 = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.product_variant_id.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        sale_line_1 = sale_order_1.order_line[0]
        self.assertEqual(sale_line_1.customer_lead, 5)  # Customer lead time only
        sale_order_1.action_confirm()  # Reserve the only stock
        sale_order_2 = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.product_variant_id.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        sale_line = sale_order_2.order_line[0]
        self.assertEqual(sale_line.customer_lead, 15)  # 5 + 10

        # Add incoming stock that arrives before the supplier lead time
        self.env["purchase.order"].create(
            {
                "partner_id": self.seller.id,
                "date_order": datetime.datetime.now(),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.product_variant_id.id,
                            "product_qty": 20,  # Ample stock
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        ).button_confirm()
        sale_line._compute_customer_lead()
        self.assertEqual(sale_line.customer_lead, 15)  # Incoming stock ignored
