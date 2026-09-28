from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductAlternative(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Attribute = cls.env["product.attribute"]
        Value = cls.env["product.attribute.value"]
        Template = cls.env["product.template"]

        # Color / Size -> 'always' attributes, so variants materialise.
        cls.color = Attribute.create({"name": "Color", "create_variant": "always"})
        cls.red = Value.create({"name": "Red", "attribute_id": cls.color.id})
        cls.blue = Value.create({"name": "Blue", "attribute_id": cls.color.id})
        cls.size = Attribute.create({"name": "Size", "create_variant": "always"})
        cls.small = Value.create({"name": "S", "attribute_id": cls.size.id})
        cls.large = Value.create({"name": "L", "attribute_id": cls.size.id})

        # Source has Color -> 2 variants (Red, Blue), so source-side scoping
        # is meaningful.
        cls.source = Template.create(
            {
                "name": "Source",
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": cls.color.id,
                            "value_ids": [Command.set([cls.red.id, cls.blue.id])],
                        }
                    ),
                ],
            }
        )
        cls.target = Template.create(
            {
                "name": "Target",
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": cls.color.id,
                            "value_ids": [Command.set([cls.red.id, cls.blue.id])],
                        }
                    ),
                    Command.create(
                        {
                            "attribute_id": cls.size.id,
                            "value_ids": [Command.set([cls.small.id, cls.large.id])],
                        }
                    ),
                ],
            }
        )
        # 2 colors x 2 sizes = 4 variants materialise automatically.

        # Dynamic template -> no variant materialised up front.
        cls.dyn_attr = Attribute.create(
            {"name": "DynColor", "create_variant": "dynamic"}
        )
        cls.dyn_red = Value.create({"name": "DRed", "attribute_id": cls.dyn_attr.id})
        cls.dyn_blue = Value.create({"name": "DBlue", "attribute_id": cls.dyn_attr.id})
        cls.dyn_target = Template.create(
            {
                "name": "DynTarget",
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": cls.dyn_attr.id,
                            "value_ids": [
                                Command.set([cls.dyn_red.id, cls.dyn_blue.id])
                            ],
                        }
                    ),
                ],
            }
        )

    @classmethod
    def _ptav(cls, template, value):
        return template.attribute_line_ids.product_template_value_ids.filtered(
            lambda p: p.product_attribute_value_id == value
        )

    def _variant(self, template, *values):
        ptavs = self.env["product.template.attribute.value"]
        for value in values:
            ptavs |= self._ptav(template, value)
        return template.product_variant_ids.filtered(
            lambda v: ptavs <= v.product_template_attribute_value_ids
        )

    def _has_value_domain(self, template, *values):
        """Domain string matching variants carrying every listed value."""
        leaves = [
            ("product_template_attribute_value_ids", "in", self._ptav(template, v).ids)
            for v in values
        ]
        return repr(leaves)

    def _alternative(self, **vals):
        vals.setdefault("product_tmpl_id", self.source.id)
        # In domain mode the alternative is defined purely by the domain and
        # no alternative template is allowed.
        if vals.get("mode", "specific") != "domain":
            vals.setdefault("alternative_tmpl_id", self.target.id)
        return self.env["product.alternative"].create(vals)

    def test_empty_matches_all_variants(self):
        alt = self._alternative()
        self.assertEqual(
            alt._get_alternative_variants(), self.target.product_variant_ids
        )
        self.assertEqual(len(alt._get_alternative_variants()), 4)

    def test_domain_filters_one_attribute(self):
        # Red only -> Red/S and Red/L, sizes unconstrained.
        alt = self._alternative(
            mode="domain",
            alternative_domain=self._has_value_domain(self.target, self.red),
        )
        result = alt._get_alternative_variants()
        self.assertEqual(result, self._variant(self.target, self.red))
        self.assertEqual(len(result), 2)

    def test_domain_cross_attribute_is_and(self):
        # Red AND Small -> exactly one variant.
        alt = self._alternative(
            mode="domain",
            alternative_domain=self._has_value_domain(
                self.target, self.red, self.small
            ),
        )
        result = alt._get_alternative_variants()
        self.assertEqual(len(result), 1)
        self.assertEqual(result, self._variant(self.target, self.red, self.small))

    def test_domain_can_pin_single_variant_by_id(self):
        # A domain subsumes the hyper-specific case.
        variant = self._variant(self.target, self.blue, self.large)
        alt = self._alternative(
            mode="domain", alternative_domain=repr([("id", "=", variant.id)])
        )
        self.assertEqual(alt._get_alternative_variants(), variant)

    def test_domain_bounded_to_alternative_template(self):
        # An empty domain never leaks variants of other templates.
        alt = self._alternative()
        self.assertTrue(
            all(
                v.product_tmpl_id == self.target
                for v in alt._get_alternative_variants()
            )
        )

    def test_source_scoping_per_variant(self):
        # Source Red variants -> Target Blue variants only.
        self._alternative(
            mode="domain",
            product_domain=self._has_value_domain(self.source, self.red),
            alternative_domain=self._has_value_domain(self.target, self.blue),
        )
        source_red = self._variant(self.source, self.red)
        source_blue = self._variant(self.source, self.blue)
        expected = self._variant(self.target, self.blue)

        self.assertEqual(source_red._get_alternative_products(), expected)
        self.assertEqual(len(expected), 2)
        self.assertFalse(source_blue._get_alternative_products())

    def test_empty_source_domain_applies_to_all_variants(self):
        self._alternative(
            mode="domain",
            alternative_domain=self._has_value_domain(self.target, self.red),
        )
        expected = self._variant(self.target, self.red)
        for variant in self.source.product_variant_ids:
            self.assertEqual(variant._get_alternative_products(), expected)

    def test_dynamic_empty_when_no_variant_materialised(self):
        alt = self._alternative(
            mode="domain",
            alternative_domain=repr([("product_tmpl_id", "=", self.dyn_target.id)]),
        )
        self.assertFalse(alt._get_alternative_variants())
        self.assertFalse(self.dyn_target.product_variant_ids)

    def test_dynamic_matches_once_materialised(self):
        combination = self._ptav(self.dyn_target, self.dyn_red)
        variant = self.dyn_target._create_product_variant(combination)
        self.assertTrue(variant)
        alt = self._alternative(
            mode="domain",
            alternative_domain=repr(
                [("product_template_attribute_value_ids", "in", combination.ids)]
            ),
        )
        self.assertEqual(alt._get_alternative_variants(), variant)

    def test_domain_without_alternative_template_matches_any_product(self):
        # No alternative template in domain mode: the domain is matched against
        # variants of any product, not bounded to a single template.
        alt = self._alternative(
            mode="domain",
            alternative_tmpl_id=False,
            alternative_domain=repr(
                [("product_tmpl_id", "in", [self.source.id, self.target.id])]
            ),
        )
        expected = self.source.product_variant_ids | self.target.product_variant_ids
        self.assertEqual(alt._get_alternative_variants(), expected)
        self.assertEqual(len(expected), 6)

    def test_domain_without_alternative_template_allowed(self):
        # Domain mode does not require an alternative template.
        alt = self._alternative(mode="domain", alternative_tmpl_id=False)
        self.assertTrue(alt)

    def test_specific_mode_requires_alternative_template(self):
        with self.assertRaises(ValidationError):
            self._alternative(mode="specific", alternative_tmpl_id=False)

    def test_domain_mode_forbids_alternative_template(self):
        with self.assertRaises(ValidationError):
            self._alternative(mode="domain", alternative_tmpl_id=self.target.id)

    def test_cannot_be_alternative_of_self(self):
        with self.assertRaises(ValidationError):
            self._alternative(mode="specific", alternative_tmpl_id=self.source.id)

    def test_matched_variant_count(self):
        alt = self._alternative(
            mode="domain",
            alternative_domain=self._has_value_domain(self.target, self.red),
        )
        self.assertEqual(alt.matched_variant_count, 2)

    def test_specific_mode_template_to_template(self):
        self._alternative(mode="specific")
        for variant in self.source.product_variant_ids:
            self.assertEqual(
                variant._get_alternative_products(),
                self.target.product_variant_ids,
            )

    def test_specific_mode_pins_target_variants(self):
        targets = self._variant(self.target, self.blue, self.large) | self._variant(
            self.target, self.red, self.small
        )
        self._alternative(
            mode="specific",
            alternative_variant_ids=[Command.set(targets.ids)],
        )
        for variant in self.source.product_variant_ids:
            self.assertEqual(variant._get_alternative_products(), targets)

    def test_specific_mode_pins_source_variant(self):
        source_red = self._variant(self.source, self.red)
        source_blue = self._variant(self.source, self.blue)
        self._alternative(
            mode="specific",
            product_variant_ids=[Command.set(source_red.ids)],
        )
        self.assertEqual(
            source_red._get_alternative_products(), self.target.product_variant_ids
        )
        self.assertFalse(source_blue._get_alternative_products())

    def test_specific_mode_pins_both_sides(self):
        source_red = self._variant(self.source, self.red)
        source_blue = self._variant(self.source, self.blue)
        target_variant = self._variant(self.target, self.blue, self.small)
        self._alternative(
            mode="specific",
            product_variant_ids=[Command.set(source_red.ids)],
            alternative_variant_ids=[Command.set(target_variant.ids)],
        )
        self.assertEqual(source_red._get_alternative_products(), target_variant)
        self.assertFalse(source_blue._get_alternative_products())

    def test_specific_source_variant_must_belong_to_product(self):
        with self.assertRaises(ValidationError):
            self._alternative(
                mode="specific",
                product_variant_ids=[
                    Command.set(self._variant(self.target, self.red, self.small).ids)
                ],
            )

    def test_specific_alternative_variant_must_belong(self):
        with self.assertRaises(ValidationError):
            self._alternative(
                mode="specific",
                alternative_variant_ids=[
                    Command.set(self._variant(self.source, self.red).ids)
                ],
            )

    def test_invalid_domain_ignored_in_specific_mode(self):
        # Domain validation is skipped when the mode is not 'domain'.
        alt = self._alternative(mode="specific", alternative_domain="not a domain")
        self.assertTrue(alt)
