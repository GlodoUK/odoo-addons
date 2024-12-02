from odoo.exceptions import ValidationError

from odoo.addons.product_commingle.tests.common import CommonCommingleCase


class TestCommingle(CommonCommingleCase):
    def test_recursive(self):
        with self.assertRaises(ValidationError):
            self.product_bolt_equiv.write(
                {
                    "commingled_ids": [
                        (0, 0, {"product_id": self.product_bolt_equiv.id})
                    ],
                }
            )
