from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo import fields
from odoo.tests import tagged

from .common import ProductConformityCommon


@tagged("post_install", "-at_install")
class TestProductConformityAlert(ProductConformityCommon):
    def _create_alert(self, date_start, reason="time"):
        return self.env["product.conformity.alert"].create(
            {
                "product_id": self.product_tmpl_unit.product_variant_id.id,
                "date_start": date_start,
                "date_end": date_start + relativedelta(days=30),
                "reason": reason,
            }
        )

    @freeze_time("2025-10-10 15:30:00")
    def test_action_pass(self):
        date_start = fields.Datetime.now()
        alert_id = self._create_alert(date_start)

        self.assertEqual(alert_id.state, "open")
        self.assertFalse(alert_id.date_acknowledge)

        alert_id.action_pass()

        self.assertEqual(alert_id.state, "pass")
        self.assertEqual(alert_id.date_acknowledge, date_start)

    @freeze_time("2025-10-10 15:30:00")
    def test_action_fail(self):
        date_start = fields.Datetime.now()
        alert_id = self._create_alert(date_start)

        self.assertEqual(alert_id.state, "open")

        alert_id.action_fail()

        self.assertEqual(alert_id.state, "fail")
        self.assertEqual(alert_id.date_acknowledge, date_start)

    @freeze_time("2025-10-10 15:30:00")
    def test_action_suppress(self):
        date_start = fields.Datetime.now()
        alert_id = self._create_alert(date_start)

        self.assertEqual(alert_id.state, "open")

        alert_id.action_suppress()

        self.assertEqual(alert_id.state, "suppress")
        self.assertEqual(alert_id.date_acknowledge, date_start)
