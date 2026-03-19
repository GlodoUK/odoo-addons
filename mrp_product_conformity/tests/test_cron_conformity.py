from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo import fields
from odoo.tests import tagged

from .common import ProductConformityCommon


@tagged("post_install", "-at_install")
class TestCronConformity(ProductConformityCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_dozen.conformity_enabled = True
        cls.product_unit.conformity_enabled = True

    @freeze_time("2025-01-01 03:00:00")
    def test_cron_no_expired_product(self):
        """
        Test cron doesn't create alerts when no products have expired
        """
        self.product_unit.write(
            {
                "conformity_start_date": fields.Datetime.now(),
            }
        )

        self.assertEqual(
            self.product_unit.conformity_end_date,
            fields.Datetime.now() + relativedelta(months=1),
            "Conformity end date should be one month in the future",
        )

        self.env["product.product"]._cron_conformity()

        # Should have no alerts
        self.assertEqual(
            self._alert_count(self.product_unit),
            0,
            "No alerts should be created for non-expired products",
        )

    @freeze_time("2025-03-01 00:00:00")
    def test_cron_multiple_expired_products(self):
        """
        Test cron handles multiple expired products and creates multiple alerts
        """

        start_date = fields.Datetime.now() - relativedelta(months=1)

        for product in [self.product_dozen, self.product_unit]:
            product.write(
                {
                    "conformity_start_date": start_date,
                    "conformity_interval_type": "weeks",
                }
            )

            self.assertLess(
                product.conformity_end_date,
                fields.Datetime.now(),
                f"Product {product.name} conformity should be expired",
            )

        self.env["product.product"]._cron_conformity()

        for product in [self.product_dozen, self.product_unit]:
            self.assertEqual(
                self._alert_count(product),
                1,
                f"Product {product.name} should have exactly one alert",
            )

    @freeze_time("2025-02-15 00:00:00")
    def test_cron_comprehensive_workflow(self):
        """
        Comprehensive test covering:
        - Single expired product creates one alert
        - Alert includes MRP productions within period
        - Alert excludes MRP productions outside period
        - Alert has correct date_start and date_end
        - Alert has reason='time'
        - conformity_start_date updates to conformity_end_date
        - conformity_end_date recomputes correctly
        - No duplicate alerts on repeated cron runs
        """

        start_date = fields.Datetime.now() - relativedelta(weeks=6)

        self.product_unit.write(
            {
                "conformity_start_date": start_date,
            }
        )

        self.assertEqual(
            self.product_unit.conformity_end_date,
            start_date + relativedelta(months=1),
            "Initial conformity end date should be computed correctly",
        )

        self.assertLess(
            self.product_unit.conformity_end_date,
            fields.Datetime.now(),
            "Product conformity should be expired",
        )

        # Create production OUTSIDE the conformity window
        production_outside = self._create_production_done(
            self.product_unit,
            25.0,
            date_finished=start_date - relativedelta(days=5),
        )

        # Create production INSIDE the conformity window
        production_inside = self._create_production_done(
            self.product_unit,
            50.0,
            date_finished=start_date + relativedelta(days=10),
        )

        self.env["product.product"]._cron_conformity()

        self.assertEqual(
            self._alert_count(self.product_unit),
            1,
            "Exactly one alert should be created for expired product",
        )

        alert = self.env["product.conformity.alert"].search(
            [
                ("product_id", "=", self.product_unit.id),
                ("state", "=", "open"),
            ]
        )

        self.assertEqual(
            alert.reason,
            "time",
            "Alert should have reason='time' for time-based expiry",
        )

        self.assertEqual(
            alert.date_start,
            start_date,
            "Alert date_start should match product conformity_start_date",
        )

        # Verify alert has correct date_end
        self.assertEqual(
            alert.date_end,
            start_date + relativedelta(months=1),
            "Alert date_end should match product conformity_end_date",
        )

        self.assertEqual(
            len(alert.mrp_production_ids),
            1,
            "Alert should include exactly one production",
        )

        self.assertIn(
            production_inside,
            alert.mrp_production_ids,
            "Alert should include production from inside the conformity window",
        )

        self.assertNotIn(
            production_outside,
            alert.mrp_production_ids,
            "Alert should NOT include production from outside the conformity window",
        )

        self.assertEqual(
            self.product_unit.conformity_start_date,
            start_date + relativedelta(months=1),
            "conformity_start_date should roll forward to old conformity_end_date",
        )

        self.assertEqual(
            self.product_unit.conformity_end_date,
            start_date + relativedelta(months=2),
            "conformity_end_date should be recomputed based on new start date",
        )

        # Run cron second time
        self.env["product.product"]._cron_conformity()

        self.assertEqual(
            self._alert_count(self.product_unit),
            1,
            "Should not create duplicate alerts - new period is not expired yet",
        )
