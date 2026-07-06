from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    reception_steps = fields.Selection(
        selection_add=[("one_half_step", "Receive then Store manually (1.5 steps)")],
        ondelete={"one_half_step": "set default"},
    )

    def get_rules_dict(self):
        """Add the routing for the one-and-a-half-step receipt.

        It is a two-step receipt without the automatic store move: goods are
        pulled from the vendor into Input and then transferred to Stock
        manually. We derive it from the live ``two_steps`` entry by dropping
        its final (Input -> Stock) store rule, so we stay consistent with
        whatever ``purchase_stock``/``mrp`` have layered on top of the base
        two-step routing:

        - plain stock: two_steps == [vendor -> Input (pull),
          Input -> Stock (push)] -> one_half_step == [vendor -> Input (pull)]
        - with Buy installed, the vendor pull is replaced by the global Buy
          rule, so two_steps == [Input -> Stock (push)] and
          one_half_step == [] (see ``_get_receive_rules_dict``).
        """
        result = super().get_rules_dict()
        for warehouse in self:
            wh_rules = result.get(warehouse.id)
            if wh_rules and "two_steps" in wh_rules:
                wh_rules["one_half_step"] = wh_rules["two_steps"][:-1]
        return result

    def _get_receive_rules_dict(self):
        """No automatic store step for the one-and-a-half-step receipt.

        Used by ``purchase_stock``/``mrp`` when the initial pull is provided by
        a global rule (Buy/Manufacture); the receipt lands in Input and stays
        there until moved manually, so there are no onward rules.
        """
        result = super()._get_receive_rules_dict()
        result["one_half_step"] = []
        return result

    def _get_route_name(self, route_type):
        if route_type == "one_half_step":
            return self.env._("Receive in 2 steps but store manually (input + stock)")
        return super()._get_route_name(route_type)

    def _get_picking_type_update_values(self):
        """Point the Storage operation type at Input.

        The base implementation only sources Storage from Input for
        ``two_steps`` (otherwise it uses Quality Control, which is inactive
        here). For the one-and-a-half-step receipt the manual store move runs
        Input -> Stock, so the operation type must default to Input as source.
        """
        values = super()._get_picking_type_update_values()
        if self.reception_steps == "one_half_step":
            input_loc, _dummy = self._get_input_output_locations(
                self.reception_steps, self.delivery_steps
            )
            values["store_type_id"]["default_location_src_id"] = input_loc.id
        return values
