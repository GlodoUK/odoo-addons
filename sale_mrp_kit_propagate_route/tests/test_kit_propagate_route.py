from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestKitPropagateRoute(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Warehouse = cls.env["stock.warehouse"]
        cls.customers = cls.env.ref("stock.stock_location_customers")
        cls.main = Warehouse.create(
            {"name": "SMKPR Main", "code": "SMKP1", "delivery_steps": "ship_only"}
        )
        cls.other = Warehouse.create(
            {"name": "SMKPR Other", "code": "SMKP2", "delivery_steps": "ship_only"}
        )
        # Like "Direct Ship from Anglesey Road": not warehouse-scoped, so it
        # applies on the main warehouse's orders too.
        cls.direct_ship_other = cls.env["stock.route"].create(
            {
                "name": "SMKPR Direct Ship from Other",
                "product_selectable": True,
                "sale_selectable": True,
                "sequence": 3,
                "rule_ids": [
                    Command.create(
                        {
                            "name": "SMKP2: Stock -> Customers",
                            "action": "pull",
                            "procure_method": "make_to_stock",
                            "location_src_id": cls.other.lot_stock_id.id,
                            "location_dest_id": cls.customers.id,
                            "picking_type_id": cls.other.out_type_id.id,
                        }
                    )
                ],
            }
        )
        # Its own category, so the live database's category routes stay out.
        cls.categ = cls.env["product.category"].create({"name": "SMKPR"})
        cls.component_other = cls._product(
            "SMKPR-COMP-OTHER", routes=cls.direct_ship_other
        )
        cls.component_plain = cls._product("SMKPR-COMP-PLAIN")
        cls.partner = cls.env["res.partner"].create({"name": "SMKPR Customer"})

    @classmethod
    def _product(cls, code, routes=None):
        return cls.env["product.product"].create(
            {
                "name": code,
                "default_code": code,
                "is_storable": True,
                "categ_id": cls.categ.id,
                "route_ids": [Command.set(routes.ids if routes else [])],
            }
        )

    @classmethod
    def _kit(cls, code, routes=None, propagate=True, components=None):
        kit = cls._product(code, routes=routes)
        cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": kit.product_tmpl_id.id,
                "type": "phantom",
                "sale_kit_propagate_route": propagate,
                "bom_line_ids": [
                    Command.create({"product_id": component.id, "product_qty": 1})
                    for component in components
                    or (cls.component_other, cls.component_plain)
                ],
            }
        )
        return kit

    def _sell(self, product, routes=None):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.main.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": 1,
                            "route_ids": [Command.set(routes.ids if routes else [])],
                        }
                    )
                ],
            }
        )
        order.action_confirm()
        return order.picking_ids.move_ids

    def _source_by_product(self, moves):
        return {move.product_id: move.location_id for move in moves}

    def test_kit_with_route_ships_every_component_by_it(self):
        kit = self._kit("SMKPR-KIT-OTHER", routes=self.direct_ship_other)
        sources = self._source_by_product(self._sell(kit))
        self.assertEqual(sources[self.component_other], self.other.lot_stock_id)
        self.assertEqual(sources[self.component_plain], self.other.lot_stock_id)

    def test_kit_without_route_ships_from_the_warehouse(self):
        """A component's own direct-ship route doesn't pull it out of a kit
        that ships from the order's warehouse."""
        kit = self._kit("SMKPR-KIT-PLAIN")
        sources = self._source_by_product(self._sell(kit))
        self.assertEqual(sources[self.component_other], self.main.lot_stock_id)
        self.assertEqual(sources[self.component_plain], self.main.lot_stock_id)

    def test_component_sold_alone_keeps_its_route(self):
        sources = self._source_by_product(self._sell(self.component_other))
        self.assertEqual(sources[self.component_other], self.other.lot_stock_id)

    def test_line_route_wins(self):
        kit = self._kit("SMKPR-KIT-LINE")
        sources = self._source_by_product(
            self._sell(kit, routes=self.direct_ship_other)
        )
        self.assertEqual(sources[self.component_other], self.other.lot_stock_id)
        self.assertEqual(sources[self.component_plain], self.other.lot_stock_id)

    def test_bom_switched_off_is_core(self):
        kit = self._kit("SMKPR-KIT-OFF", propagate=False)
        sources = self._source_by_product(self._sell(kit))
        self.assertEqual(sources[self.component_other], self.other.lot_stock_id)
        self.assertEqual(sources[self.component_plain], self.main.lot_stock_id)

    def test_procurement_outside_a_sale_is_core(self):
        kit = self._kit("SMKPR-KIT-NOSALE")
        Rule = self.env["stock.rule"]
        Rule.run(
            [
                Rule.Procurement(
                    kit,
                    1,
                    kit.uom_id,
                    self.customers,
                    "SMKPR-NOSALE",
                    "SMKPR-NOSALE",
                    self.env.company,
                    {"warehouse_id": self.main},
                )
            ]
        )
        moves = self.env["stock.move"].search([("origin", "=", "SMKPR-NOSALE")])
        sources = self._source_by_product(moves)
        self.assertEqual(sources[self.component_other], self.other.lot_stock_id)
        self.assertEqual(sources[self.component_plain], self.main.lot_stock_id)

    def _nested_kit(self, code, outer_routes=None, inner_routes=None, **kwargs):
        """A kit of a plain component and an inner kit holding the other
        two, so the three end up side by side once mrp explodes it."""
        component_nested = self._product(f"{code}-COMP")
        inner = self._kit(f"{code}-INNER", routes=inner_routes)
        outer = self._kit(
            code,
            routes=outer_routes,
            components=(inner, component_nested),
            **kwargs,
        )
        return outer, component_nested

    def test_nested_kit_follows_the_kit_sold(self):
        """The inner kit's route counts for nothing: the kit that was sold
        has none, so everything ships from the warehouse."""
        kit, component_nested = self._nested_kit(
            "SMKPR-NEST-PLAIN", inner_routes=self.direct_ship_other
        )
        sources = self._source_by_product(self._sell(kit))
        self.assertEqual(sources[self.component_other], self.main.lot_stock_id)
        self.assertEqual(sources[self.component_plain], self.main.lot_stock_id)
        self.assertEqual(sources[component_nested], self.main.lot_stock_id)

    def test_nested_kit_takes_the_route_of_the_kit_sold(self):
        kit, component_nested = self._nested_kit(
            "SMKPR-NEST-OTHER", outer_routes=self.direct_ship_other
        )
        sources = self._source_by_product(self._sell(kit))
        self.assertEqual(sources[self.component_other], self.other.lot_stock_id)
        self.assertEqual(sources[self.component_plain], self.other.lot_stock_id)
        self.assertEqual(sources[component_nested], self.other.lot_stock_id)

    def test_nested_kit_sold_switched_off_is_core(self):
        """The inner kit's BoM being on doesn't matter when the kit sold is
        off."""
        kit, component_nested = self._nested_kit(
            "SMKPR-NEST-OFF", inner_routes=self.direct_ship_other, propagate=False
        )
        sources = self._source_by_product(self._sell(kit))
        self.assertEqual(sources[self.component_other], self.other.lot_stock_id)
        self.assertEqual(sources[self.component_plain], self.main.lot_stock_id)
        self.assertEqual(sources[component_nested], self.main.lot_stock_id)
