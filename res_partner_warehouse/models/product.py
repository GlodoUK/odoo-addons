from odoo import api, fields, models
from odoo.tools import float_compare


class ProductTemplate(models.Model):
    _inherit = "product.template"

    res_partner_warehouse_qty = fields.Float(
        compute="_compute_res_partner_warehouse_qty",
        string="Partner Warehouse Quantity",
    )

    def _compute_res_partner_warehouse_qty(self):
        for record in self:
            record.res_partner_warehouse_qty = sum(
                record.product_variant_ids.mapped("res_partner_warehouse_qty")
            )

    def action_view_res_partner_warehouse_quants(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "res_partner_warehouse.actions_res_partner_warehouse_quant_act_window"
        )
        action["domain"] = [
            ("product_id", "in", self.mapped("product_variant_ids").ids)
        ]
        return action


class ProductProduct(models.Model):
    _inherit = "product.product"

    res_partner_warehouse_qty = fields.Float(
        compute="_compute_res_partner_warehouse_qty",
        string="Partner Warehouse Quantity",
    )

    virtual_available_inc_partner_warehouse = fields.Float(
        compute="_compute_res_partner_warehouse_qtys",
        string="Forecasted Quantity inc. Suppliers",
    )

    qty_available_inc_partner_warehouse = fields.Float(
        compute="_compute_res_partner_warehouse_qtys",
        string="Quantity On Hand inc. Suppliers",
    )

    free_qty_inc_partner_warehouse = fields.Float(
        compute="_compute_res_partner_warehouse_qtys",
        string="Free Quantity inc. Suppliers",
    )

    @api.depends(
        "virtual_available", "qty_available", "free_qty", "res_partner_warehouse_qty"
    )
    def _compute_res_partner_warehouse_qtys(self):
        for record in self:
            record.virtual_available_inc_partner_warehouse = (
                record.virtual_available + record.res_partner_warehouse_qty
            )
            record.qty_available_inc_partner_warehouse = (
                record.qty_available + record.res_partner_warehouse_qty
            )
            record.free_qty_inc_partner_warehouse = (
                record.free_qty + record.res_partner_warehouse_qty
            )

    def _compute_res_partner_warehouse_qty(self):
        quants_dict = self.env["res.partner.warehouse.quant"]._get_available_quantities(
            self
        )

        for record in self:
            record.res_partner_warehouse_qty = quants_dict.get(record.id)

    def action_view_res_partner_warehouse_quants(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "res_partner_warehouse.actions_res_partner_warehouse_quant_act_window"
        )
        action["domain"] = [("product_id", "in", self.ids)]
        return action

    def _select_seller(
        self, partner_id=False, quantity=0.0, date=None, uom_id=False, params=False
    ):
        self.ensure_one()

        if not self.user_has_groups("res_partner_warehouse.group_select_seller"):
            return super()._select_seller(partner_id, quantity, date, uom_id, params)

        if date is None:
            date = fields.Date.context_today(self)
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )

        res = self.env["product.supplierinfo"]
        sellers = self._prepare_sellers(params)
        sellers = sellers.filtered(
            lambda s: not s.company_id or s.company_id.id == self.env.company.id
        )
        for seller in sellers:
            # Set quantity in UoM of seller
            quantity_uom_seller = quantity
            if quantity_uom_seller and uom_id and uom_id != seller.product_uom:
                quantity_uom_seller = uom_id._compute_quantity(
                    quantity_uom_seller, seller.product_uom
                )

            if (
                quantity is not None
                and seller.res_partner_warehouse_id
                and float_compare(
                    seller.res_partner_warehouse_id._get_available_quantity(
                        self, seller.product_uom
                    ),
                    quantity_uom_seller,
                    precision_digits=precision,
                )
                == -1
            ):
                # if there's not enough in this res_partner_warehouse then skip
                # to the next record immediately
                continue

            if seller.date_start and seller.date_start > date:
                continue
            if seller.date_end and seller.date_end < date:
                continue
            if partner_id and seller.name not in [partner_id, partner_id.parent_id]:
                continue
            if (
                quantity is not None
                and float_compare(
                    quantity_uom_seller, seller.min_qty, precision_digits=precision
                )
                == -1
            ):
                continue
            if seller.product_id and seller.product_id != self:
                continue
            if not res or res.name == seller.name:
                res |= seller
        return res.sorted("price")[:1]
