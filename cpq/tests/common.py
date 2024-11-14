from odoo.tests.common import TransactionCase


class TestCpqCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestCpqCommon, cls).setUpClass()

        cls.prod_attrib_colour = cls.env["product.attribute"].create({"name": "Colour"})
        cls.prod_attrib_colour_red = cls.env["product.attribute.value"].create(
            {"name": "red", "attribute_id": cls.prod_attrib_colour.id, "sequence": 1}
        )
        cls.prod_attrib_colour_blue = cls.env["product.attribute.value"].create(
            {"name": "blue", "attribute_id": cls.prod_attrib_colour.id, "sequence": 2}
        )
        cls.prod_attrib_colour_green = cls.env["product.attribute.value"].create(
            {"name": "green", "attribute_id": cls.prod_attrib_colour.id, "sequence": 3}
        )

        cls.prod_attrib_colour_custom = cls.env["product.attribute.value"].create(
            {
                "name": "custom",
                "attribute_id": cls.prod_attrib_colour.id,
                "is_custom": True,
                "cpq_custom_type": "char",
                "sequence": 4,
            }
        )

        cls.prod_attrib_size = cls.env["product.attribute"].create({"name": "size"})
        cls.prod_attrib_size_small = cls.env["product.attribute.value"].create(
            {"name": "Small", "attribute_id": cls.prod_attrib_size.id, "sequence": 1}
        )
        cls.prod_attrib_size_medium = cls.env["product.attribute.value"].create(
            {"name": "Medium", "attribute_id": cls.prod_attrib_size.id, "sequence": 2}
        )
        cls.prod_attrib_size_large = cls.env["product.attribute.value"].create(
            {"name": "Large", "attribute_id": cls.prod_attrib_size.id, "sequence": 3}
        )

        cls.prod_attrib_size_custom = cls.env["product.attribute.value"].create(
            {
                "name": "custom",
                "attribute_id": cls.prod_attrib_size.id,
                "is_custom": True,
                "cpq_custom_type": "integer",
                "sequence": 4,
            }
        )
