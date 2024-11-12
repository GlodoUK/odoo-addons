from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    meta_parent_line_id = fields.Many2one(
        "sale.order.line",
        "Meta Parent",
        readonly=True,
        ondelete="cascade",
    )

    meta_child_line_ids = fields.One2many(
        "sale.order.line",
        "meta_parent_line_id",
        "Meta Child",
        readonly=True,
    )

    meta_tmpl_line_id = fields.Many2one(
        "product.template.meta.line", ondelete="set null"
    )

    meta_visible_to_customer = fields.Boolean(
        compute="_compute_meta_visible_to_customer"
    )

    qty_delivered_method = fields.Selection(
        selection_add=[("meta", "Meta")], ondelete={"meta": "set manual"}
    )

    qty_delivered = fields.Float(recursive=True)

    @api.depends(
        "meta_tmpl_line_id.parent_id.meta_visible_to_customer",
    )
    def _compute_meta_visible_to_customer(self):
        for record in self:
            if record.meta_tmpl_line_id:
                record.meta_visible_to_customer = (
                    record.meta_tmpl_line_id.parent_id.meta_visible_to_customer
                    != "hide"
                )
                continue

            record.meta_visible_to_customer = True

    def _explode_meta_product(self):
        self.ensure_one()

        if self.env.context.get("skip_explode_meta_product"):
            return

        if self.product_id.type != "meta":
            return

        vals = []

        todo = self.product_id.meta_product_tmpl_line_ids.mapped(
            lambda m: m._get_sale_order_line_vals(self)
        )

        seen = self.env["sale.order.line"]

        for val in todo:
            existing = fields.first(
                self.meta_child_line_ids.filtered(
                    lambda line: line.meta_tmpl_line_id.id
                    == val.get("meta_tmpl_line_id")
                )
            )

            if existing:
                existing.write(val)
                seen |= existing
                continue

            vals.append(val)

        if vals:
            seen |= self.create(vals)

        name = self.get_sale_order_line_multiline_description_sale(self.product_id)
        children = "\n".join(
            seen.mapped(
                lambda l: self.get_sale_order_line_multiline_description_sale(
                    l.product_id
                )
            )
        )

        self.name = f"{name}\n{children}"

        return seen

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._explode_meta_product()
        return record

    def write(self, vals):
        res = super().write(vals)
        if "product_id" in vals or "product_uom_qty" in vals:
            for record in self:
                record._explode_meta_product()

        if "sequence" in vals:
            for record in self:
                record.meta_child_line_ids.write({"sequence": record.sequence})

        return res

    @api.onchange(
        "product_id",
        "product_uom_qty",
        "product_uom",
        "price_unit",
        "discount",
        "name",
        "tax_id",
    )
    def _onchange_ensure_no_modify(self):
        # prevent edits if this line is a child
        if self._origin.meta_parent_line_id or self.meta_parent_line_id:
            raise UserError(
                _(
                    "You can not change this line because is part of a meta"
                    " product included in this order"
                )
            )

    @api.depends("product_id.type")
    def _compute_qty_delivered_method(self):
        res = super()._compute_qty_delivered_method()
        for line in self.filtered(lambda l: l.product_id.type == "meta"):
            line.qty_delivered_method = "meta"
        return res

    @api.depends("meta_child_line_ids.qty_delivered")
    def _compute_qty_delivered(self):
        res = super()._compute_qty_delivered()
        for record in self.filtered(lambda l: l.qty_delivered_method == "meta"):
            if all(
                c.qty_delivered >= record.product_uom_qty
                for c in record.meta_child_line_ids
            ):
                record.qty_delivered = record.product_uom_qty
            else:
                record.qty_delivered = 0.0
        return res

    @api.depends(
        "state", "product_uom_qty", "qty_delivered", "qty_to_invoice", "qty_invoiced"
    )
    def _compute_invoice_status(self):
        res = super()._compute_invoice_status()
        for record in self.filtered(lambda l: not l.meta_visible_to_customer):
            record.invoice_status = "no"
        return res

    @api.depends("qty_invoiced", "qty_delivered", "product_uom_qty", "order_id.state")
    def _get_to_invoice_qty(self):
        res = super()._get_to_invoice_qty()
        for record in self.filtered(lambda l: not l.meta_visible_to_customer):
            record.qty_to_invoice = 0.0
        return res
