from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleMrpPhantomExplode(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})

        cls.component_common = cls.env["product.product"].create(
            {"name": "Component Common", "type": "consu", "is_storable": True}
        )
        cls.component_a = cls.env["product.product"].create(
            {"name": "Component A", "type": "consu", "is_storable": True}
        )
        cls.component_b = cls.env["product.product"].create(
            {"name": "Component B", "type": "consu", "is_storable": True}
        )

    @classmethod
    def _create_kit(cls, name, attribute_create_variant):
        """Kit template with a 2-value attribute, phantom BoM flagged for sale
        explosion: 1 common component plus one component restricted to each
        attribute value via Apply on Variants."""
        attribute = cls.env["product.attribute"].create(
            {
                "name": f"{name} Option",
                "create_variant": attribute_create_variant,
                "value_ids": [
                    Command.create({"name": "Option A"}),
                    Command.create({"name": "Option B"}),
                ],
            }
        )
        template = cls.env["product.template"].create(
            {
                "name": name,
                "type": "consu",
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": attribute.id,
                            "value_ids": [Command.set(attribute.value_ids.ids)],
                        }
                    )
                ],
            }
        )
        ptav_a, ptav_b = template.attribute_line_ids.product_template_value_ids
        cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": template.id,
                "type": "phantom",
                "sale_explode": "always",
                "bom_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.component_common.id,
                            "product_qty": 1,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": cls.component_a.id,
                            "product_qty": 1,
                            "bom_product_template_attribute_value_ids": [
                                Command.set(ptav_a.ids)
                            ],
                        }
                    ),
                    Command.create(
                        {
                            "product_id": cls.component_b.id,
                            "product_qty": 1,
                            "bom_product_template_attribute_value_ids": [
                                Command.set(ptav_b.ids)
                            ],
                        }
                    ),
                ],
            }
        )
        return template, ptav_a, ptav_b

    def _create_order(self, line_vals):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [Command.create(line_vals)],
            }
        )

    def test_explode_no_variant_attribute(self):
        """Apply on Variants using a no_variant attribute: only the components
        matching the values selected on the order line are kept."""
        template, ptav_a, _ptav_b = self._create_kit("Kit NV", "no_variant")
        order = self._create_order(
            {
                "product_id": template.product_variant_id.id,
                "product_uom_qty": 2,
                "product_no_variant_attribute_value_ids": [Command.set(ptav_a.ids)],
            }
        )
        order.order_line.action_sale_mrp_phantom_explode()

        sections = order.order_line.filtered("display_type")
        self.assertEqual(len(sections), 1)
        self.assertEqual(
            order.order_line.product_id,
            self.component_common | self.component_a,
        )
        self.assertEqual(
            order.order_line.filtered(
                lambda line: line.product_id == self.component_a
            ).product_uom_qty,
            2,
        )

    def test_explode_real_variant_attribute(self):
        """Apply on Variants using a variant-creating attribute: only the
        components matching the ordered variant are kept."""
        template, ptav_a, _ptav_b = self._create_kit("Kit V", "always")
        variant_a = template.product_variant_ids.filtered(
            lambda product: ptav_a in product.product_template_attribute_value_ids
        )
        order = self._create_order(
            {
                "product_id": variant_a.id,
                "product_uom_qty": 1,
            }
        )
        order.order_line.action_sale_mrp_phantom_explode()

        self.assertEqual(
            order.order_line.product_id,
            self.component_common | self.component_a,
        )

    def test_component_count_no_variant_attribute(self):
        """The client-facing count matches what the explosion would produce."""
        template, ptav_a, _ptav_b = self._create_kit("Kit Count", "no_variant")
        result = template.product_variant_id.sale_mrp_phantom_explode(
            1, never_attribute_value_ids=ptav_a.ids
        )
        self.assertEqual(result["component_count"], 2)
