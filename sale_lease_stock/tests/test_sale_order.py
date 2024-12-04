from odoo.tests import tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged("post_install", "-at_install")
class TestSaleOrder(TestSaleCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.product_lease = cls.env["product.template"].create(
            {
                "lease_ok": True,
                "sale_ok": True,
                "name": "LEASE PROD",
                "default_code": "PROD_LEASE",
                "lease_pricing_ids": [
                    (
                        0,
                        0,
                        {
                            "duration": 2,
                            "unit": "months",
                            "price": 12.0,
                        },
                    )
                ],
            }
        )

    def test_lease_sale(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "partner_invoice_id": self.partner_a.id,
                "partner_shipping_id": self.partner_a.id,
                "pricelist_id": self.company_data["default_pricelist"].id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_lease.id,
                            "is_lease": True,
                            "lease_pricing_id": self.product_lease.lease_pricing_ids[
                                0
                            ].id,
                            "product_uom_qty": 1.0,
                        },
                    )
                ],
            }
        )

        sale_order.action_confirm()

        self.assertEqual(
            sale_order.lease_schedule_count,
            2,
            "there should be 2 lease schedules created",
        )
        self.assertEqual(
            sale_order.order_line.qty_to_invoice,
            0.0,
            "the lease sale order line should have 0 qty to invoice",
        )

        lease_schedule_ids = sale_order.order_line.lease_schedule_ids
        lease_schedule_ids[0].action_create_invoices()

        self.assertEqual(
            lease_schedule_ids[0].state,
            "done",
            "after creating an invoice from a lease schedule the schedule state must be done",
        )

        self.assertEqual(
            sale_order.order_line.qty_invoiced,
            0.5,
            "after invoicing 50% of the lease schedule the qty_invoiced must be 0.5",
        )

        lease_schedule_ids[1].action_create_invoices()
        self.assertEqual(
            sale_order.order_line.qty_invoiced,
            1.0,
            "after invoicing 100% of the lease schedule the qty_invoiced must be 1.0",
        )

        # TODO: add credit note check/support tomorrow morning
