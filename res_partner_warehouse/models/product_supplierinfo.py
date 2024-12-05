from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    res_partner_warehouse_id = fields.Many2one(
        "res.partner.warehouse",
        domain="[('partner_id', '=', name)]",
        string="Partner Warehouse",
    )

    res_partner_warehouse_quantity = fields.Float(
        compute="_compute_res_partner_warehouse_quantity",
        string="Partner Quantity",
    )

    require_variant = fields.Boolean(
        compute="_compute_require_variant",
        store=True,
    )

    @api.depends("product_tmpl_id.product_variant_ids", "res_partner_warehouse_id")
    def _compute_require_variant(self):
        for record in self:
            record.require_variant = (
                record.product_tmpl_id.product_variant_count > 1
                and record.res_partner_warehouse_id
            )

    def _compute_res_partner_warehouse_quantity(self):
        for record in self:
            tracked_product = record.product_id or fields.first(
                record.product_tmpl_id.product_variant_ids
            )
            if (
                not record.res_partner_warehouse_id
                or not tracked_product
                or not tracked_product.active
            ):
                record.res_partner_warehouse_quantity = False
                continue

            record.res_partner_warehouse_quantity = (
                record.res_partner_warehouse_id._get_available_quantity(
                    tracked_product,
                    uom_id=record.product_uom,
                )
            )

    @api.constrains("res_partner_warehouse_id", "name")
    def _check_res_partner_warehouse_id(self):
        for record in self.filtered(lambda r: r.res_partner_warehouse_id):
            if record.res_partner_warehouse_id.partner_id != record.name:
                raise ValidationError(
                    _("Partner on warehouse and supplier info record do not match!")
                )

    @api.constrains("res_partner_warehouse_id", "product_id")
    def _check_res_partner_warehouse_id_product_id(self):
        for record in self:
            if record.require_variant and not record.product_id:
                raise ValidationError(
                    _(
                        "Product Variant is required when Partner Warehouse is"
                        " set on a Supplier record!"
                    )
                )

    def action_view_res_partner_warehouse_quants(self):
        self.ensure_one()

        if not self.res_partner_warehouse_id:
            raise UserError(_("No partner warehouse set!"))

        return self.res_partner_warehouse_id.action_view_quants()
