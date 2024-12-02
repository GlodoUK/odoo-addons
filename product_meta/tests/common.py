from odoo.tests import TransactionCase


class TestMetaCommon(TransactionCase):
    @classmethod
    def _setup_meta_product_template(cls, vals):
        product_tmpl = cls.env["product.template"].new(vals)
        product_tmpl._onchange_meta_type()
        vals = product_tmpl._convert_to_write(product_tmpl._cache)
        return cls.env["product.template"].create(vals)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.supplier_a = cls.env["res.partner"].create(
            {
                "name": "Supplier A",
            }
        )

        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Product A",
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "name": cls.supplier_a.id,
                        },
                    ),
                ],
            }
        )

        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Product B",
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "name": cls.supplier_a.id,
                        },
                    ),
                ],
            }
        )

        cls.product_meta_1 = cls._setup_meta_product_template(
            {
                "name": "Product Meta 1",
                "type": "meta",
                "purchase_ok": False,
                "meta_product_tmpl_line_ids": [
                    (
                        0,
                        0,
                        {
                            "child_tmpl_id": cls.product_a.product_tmpl_id.id,
                            "child_variant_id": cls.product_a.id,
                            "quantity": 1.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "child_tmpl_id": cls.product_b.product_tmpl_id.id,
                            "child_variant_id": cls.product_b.id,
                            "quantity": 2.0,
                        },
                    ),
                ],
            }
        )

        cls.product_meta_2 = cls._setup_meta_product_template(
            {
                "name": "Product Meta 2",
                "type": "meta",
                "purchase_ok": False,
                "meta_product_tmpl_line_ids": [
                    (
                        0,
                        0,
                        {
                            "child_tmpl_id": cls.product_a.product_tmpl_id.id,
                            "child_variant_id": cls.product_a.id,
                            "quantity": 1.0,
                        },
                    ),
                ],
            }
        )
