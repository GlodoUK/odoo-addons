from odoo.fields import Command
from odoo.tests.common import TransactionCase


class TestCpqSaleMrpCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.env.company.anglo_saxon_accounting = True

        cls.categ_real_time = cls.env["product.category"].create(
            {
                "name": "CPQ Real Time",
                "property_valuation": "real_time",
            }
        )

        cls.uom_meter = cls.env.ref("uom.product_uom_meter")

        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

        cls.attr_cable_length = cls.env["product.attribute"].create(
            {"name": "Cable Length"}
        )
        cls.attr_val_custom_length = cls.env["product.attribute.value"].create(
            {
                "name": "Custom Length",
                "attribute_id": cls.attr_cable_length.id,
                "is_custom": True,
                "cpq_custom_type": "float",
            }
        )

        cls.attr_cable_color = cls.env["product.attribute"].create(
            {"name": "Cable Color"}
        )
        cls.attr_val_black = cls.env["product.attribute.value"].create(
            {
                "name": "Black",
                "attribute_id": cls.attr_cable_color.id,
            }
        )
        cls.attr_val_grey = cls.env["product.attribute.value"].create(
            {
                "name": "Grey",
                "attribute_id": cls.attr_cable_color.id,
            }
        )

        cls.bulk_cable = cls.env["product.product"].create(
            {
                "name": "Bulk Cat6 Cable",
                "is_storable": True,
                "standard_price": 2.0,
                "uom_id": cls.uom_meter.id,
                "categ_id": cls.categ_real_time.id,
            }
        )
        cls.rj45 = cls.env["product.product"].create(
            {
                "name": "RJ45 Connector",
                "is_storable": True,
                "standard_price": 0.0,
                "uom_id": cls.uom_unit.id,
                "categ_id": cls.categ_real_time.id,
            }
        )
        cls.boot = cls.env["product.product"].create(
            {
                "name": "Strain Relief Boot",
                "is_storable": True,
                "standard_price": 10.0,
                "uom_id": cls.uom_unit.id,
                "categ_id": cls.categ_real_time.id,
            }
        )
        cls.tie = cls.env["product.product"].create(
            {
                "name": "Velcro Tie",
                "is_storable": True,
                "standard_price": 5.0,
                "uom_id": cls.uom_unit.id,
                "categ_id": cls.categ_real_time.id,
            }
        )

        # The CPQ kit
        cls.cable_kit_tmpl = cls.env["product.template"].create(
            {
                "name": "Configured Cable Loom Kit",
                "cpq_ok": True,
                "is_storable": True,
                "categ_id": cls.categ_real_time.id,
                "uom_id": cls.uom_unit.id,
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": cls.attr_cable_length.id,
                            "value_ids": [Command.set([cls.attr_val_custom_length.id])],
                        }
                    ),
                    Command.create(
                        {
                            "attribute_id": cls.attr_cable_color.id,
                            "value_ids": [
                                Command.set(
                                    [cls.attr_val_black.id, cls.attr_val_grey.id]
                                )
                            ],
                        }
                    ),
                ],
            }
        )

        # Resolve PTAVs for the kit template.
        cls.ptav_custom_length = cls.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", cls.cable_kit_tmpl.id),
                (
                    "product_attribute_value_id",
                    "=",
                    cls.attr_val_custom_length.id,
                ),
            ],
            limit=1,
        )
        cls.ptav_black = cls.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", cls.cable_kit_tmpl.id),
                ("product_attribute_value_id", "=", cls.attr_val_black.id),
            ],
            limit=1,
        )

        cls.cable_kit_dyn_bom = cls.env["cpq.dynamic.bom"].create(
            {
                "code": "TEST CABLE KIT DYN",
                "type": "phantom",
                "product_tmpl_id": cls.cable_kit_tmpl.id,
                "product_uom_id": cls.cable_kit_tmpl.uom_id.id,
                "product_qty": 1.0,
                "bom_line_ids": [
                    Command.create(
                        {
                            "component_type": "variant",
                            "component_product_id": cls.bulk_cable.id,
                            "quantity_type": "ptav_custom_id",
                            "quantity_ptav_custom_id": cls.ptav_custom_length.id,
                            "condition_type": "always",
                            "uom_id": cls.uom_meter.id,
                        }
                    ),
                    Command.create(
                        {
                            "component_type": "variant",
                            "component_product_id": cls.rj45.id,
                            "quantity_type": "fixed",
                            "quantity_fixed": 2.0,
                            "condition_type": "always",
                            "uom_id": cls.uom_unit.id,
                        }
                    ),
                    Command.create(
                        {
                            "component_type": "variant",
                            "component_product_id": cls.boot.id,
                            "quantity_type": "fixed",
                            "quantity_fixed": 2.0,
                            "condition_type": "always",
                            "uom_id": cls.uom_unit.id,
                        }
                    ),
                    Command.create(
                        {
                            "component_type": "variant",
                            "component_product_id": cls.tie.id,
                            "quantity_type": "fixed",
                            "quantity_fixed": 2.0,
                            "condition_type": "always",
                            "uom_id": cls.uom_unit.id,
                        }
                    ),
                ],
            }
        )

        cls.partner = cls.env["res.partner"].create({"name": "CPQ Test Customer"})
