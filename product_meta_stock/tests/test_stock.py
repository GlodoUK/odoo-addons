from odoo.exceptions import ValidationError

from odoo.addons.product_meta.tests.common import TestMetaCommon


class TestStock(TestMetaCommon):
    def test_no_routes(self):
        route_id = self.env["stock.location.route"].search(
            [
                ("product_selectable", "=", True),
            ],
            limit=1,
        )

        with self.assertRaises(ValidationError):
            self.product_meta_1.write({"route_ids": [(4, route_id.id, 0)]})
