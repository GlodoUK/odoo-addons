from odoo.tests.common import TransactionCase


class CommonCommingleCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_bolta = cls.env["product.product"].create(
            {
                "name": "Bolt A",
            }
        )

        cls.product_boltb = cls.env["product.product"].create(
            {
                "name": "Bolt B",
            }
        )

        cls.product_bolt_equiv = cls.env["product.product"].create(
            {
                "name": "Bolt Equiv",
                "commingled_ok": True,
                "commingled_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 1,
                            "product_id": cls.product_bolta.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 2,
                            "product_id": cls.product_boltb.id,
                        },
                    ),
                ],
            }
        )
