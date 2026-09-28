from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    reception_steps = fields.Selection(
        selection_add=[
            ("one_half_step", "Receive then Store manually (1.5 steps)"),
            (
                "two_half_step",
                "Receive, Quality Control, then Store manually (2.5 steps)",
            ),
        ],
        ondelete={"one_half_step": "set default", "two_half_step": "set default"},
    )

    def get_rules_dict(self):
        """Add the routing for the manual-store receipts.

        Both modes are a standard multi-step receipt with the automatic store
        move dropped: goods are pulled in as usual and then transferred to
        Stock manually. We derive them from the live ``two_steps``/
        ``three_steps`` entries by dropping their final store rule, so we stay
        consistent with whatever ``purchase_stock``/``mrp`` have layered on top
        of the base routing:

        - plain stock: two_steps == [vendor -> Input (pull),
          Input -> Stock (push)] -> one_half_step == [vendor -> Input (pull)]
        - with Buy installed, the vendor pull is replaced by the global Buy
          rule, so two_steps == [Input -> Stock (push)] and
          one_half_step == [] (see ``_get_receive_rules_dict``).

        The same holds for ``three_steps`` -> ``two_half_step``, which keeps
        the Input -> Quality Control leg and drops Quality Control -> Stock.
        """
        result = super().get_rules_dict()
        for warehouse in self:
            wh_rules = result.get(warehouse.id)
            if not wh_rules:
                continue
            if "two_steps" in wh_rules:
                wh_rules["one_half_step"] = wh_rules["two_steps"][:-1]
            if "three_steps" in wh_rules:
                wh_rules["two_half_step"] = wh_rules["three_steps"][:-1]
        return result

    def _get_receive_rules_dict(self):
        """No automatic store step for the manual-store receipts.

        Used by ``purchase_stock``/``mrp`` when the initial pull is provided by
        a global rule (Buy/Manufacture). For ``one_half_step`` the receipt
        lands in Input and stays there until moved manually, so there are no
        onward rules at all. For ``two_half_step`` the Input -> Quality Control
        leg still runs automatically and only the final store move is dropped.
        """
        result = super()._get_receive_rules_dict()
        result["one_half_step"] = []
        result["two_half_step"] = result["three_steps"][:-1]
        return result

    def _get_route_name(self, route_type):
        if route_type == "one_half_step":
            return self.env._("Receive in 2 steps but store manually (input + stock)")
        if route_type == "two_half_step":
            return self.env._(
                "Receive in 3 steps but store manually (input + quality + stock)"
            )
        return super()._get_route_name(route_type)

    def _get_locations_values(self, vals, code=False):
        """Keep the Quality Control location for the 2.5-step receipt.

        The base implementation only activates it for ``three_steps``, but the
        2.5-step receipt still routes Input -> Quality Control.
        """
        values = super()._get_locations_values(vals, code=code)
        reception_steps = vals.get(
            "reception_steps", self.default_get(["reception_steps"])["reception_steps"]
        )
        if reception_steps == "two_half_step":
            values["wh_qc_stock_loc_id"]["active"] = True
        return values

    def _update_location_reception(self, new_reception_step):
        """Keep the Quality Control location active on write, as above."""
        res = super()._update_location_reception(new_reception_step)
        if new_reception_step == "two_half_step":
            self.mapped("wh_qc_stock_loc_id").write({"active": True})
        return res

    def _get_picking_type_update_values(self):
        """Point the Storage operation type at the manual move's source.

        The base implementation only sources Storage from Input for
        ``two_steps`` (otherwise it uses Quality Control) and only activates
        the Quality Control operation type for ``three_steps``.

        - ``one_half_step``: the manual store move runs Input -> Stock, so
          Storage must default to Input as source (Quality Control is
          inactive here).
        - ``two_half_step``: the manual store move runs Quality Control ->
          Stock, so Storage defaults to Quality Control and the Quality
          Control operation type has to stay active for the automatic
          Input -> Quality Control leg.
        """
        values = super()._get_picking_type_update_values()
        if self.reception_steps == "one_half_step":
            input_loc, _dummy = self._get_input_output_locations(
                self.reception_steps, self.delivery_steps
            )
            values["store_type_id"]["default_location_src_id"] = input_loc.id
        elif self.reception_steps == "two_half_step":
            values["qc_type_id"]["active"] = self.active
            values["store_type_id"]["default_location_src_id"] = (
                self.wh_qc_stock_loc_id.id
            )
        return values
