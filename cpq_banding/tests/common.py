from odoo.fields import Command
from odoo.tests.common import TransactionCase


class TestCpqBandingCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        Banding = cls.env["cpq.banding"]

        cls.fabric = Banding.create({"name": "Fabric"})

        cls.cotton = Banding.create(
            {
                "name": "Cotton",
                "parent_id": cls.fabric.id,
            }
        )

        cls.cotton_white = Banding.create(
            {
                "name": "White",
                "parent_id": cls.cotton.id,
            }
        )

        cls.leather = Banding.create(
            {
                "name": "Leather",
                "parent_id": cls.fabric.id,
            }
        )

        cls.leather_tan = Banding.create(
            {
                "name": "Tan",
                "parent_id": cls.leather.id,
            }
        )

        cls.attribute = cls.env["product.attribute"].create(
            {
                "name": "Fabric Choice",
            }
        )

        cls.attr_value_banding = cls.env["product.attribute.value"].create(
            {
                "name": "Custom Banding",
                "attribute_id": cls.attribute.id,
                "is_custom": True,
                "cpq_custom_type": "banding",
                "cpq_banding_id": cls.fabric.id,
            }
        )

        cls.product_tmpl = cls.env["product.template"].create(
            {
                "name": "CPQ Banding Test Product",
                "cpq_ok": True,
                "type": "consu",
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": cls.attribute.id,
                            "value_ids": [
                                Command.set([cls.attr_value_banding.id]),
                            ],
                        }
                    ),
                ],
            }
        )
