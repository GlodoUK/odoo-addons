from odoo import _
from odoo.exceptions import UserError
from odoo.http import Controller, request, route


class ProductConfiguratorController(Controller):
    def _cpq_extract_from_combination(self, product_tmpl_id, combination):
        ptav_ids = request.env["product.template.attribute.value"].sudo()
        custom_dict = {}

        valid_product_tmpl_ptav_ids = (
            product_tmpl_id.valid_product_template_attribute_line_ids.mapped(
                "product_template_value_ids"
            )
        )

        for (k, v) in combination.items():
            ptav_id = valid_product_tmpl_ptav_ids.filtered(lambda v: v.id == int(k))
            ptav_id.ensure_one()

            if ptav_id.is_custom:
                custom_dict.update({ptav_id: v})

            ptav_ids |= ptav_id

        return (ptav_ids, custom_dict)

    @route("/cpq/<int:product_tmpl_id>/data", type="json", auth="user")
    def cpq_tmpl_data(
        self,
        product_tmpl_id,
        company_id=None,
        pricelist_id=None,
        ptav_ids=None,
    ):
        product_tmpl_id = request.env["product.template"].browse(product_tmpl_id)
        if not product_tmpl_id.cpq_ok:
            raise UserError(_("Not a CPQ enabled product!"))

        return product_tmpl_id._cpq_get_combination_info()

    @route("/cpq/<int:product_tmpl_id>/validate", type="json", auth="user")
    def cpq_validate(
        self,
        product_tmpl_id,
        combination,
    ):
        product_tmpl_id = request.env["product.template"].sudo().browse(product_tmpl_id)
        if not product_tmpl_id.cpq_ok:
            return {
                "valid": False,
                "msg": _("Not CPQ Enabled!"),
            }

        (ptav_ids, custom_dict) = self._cpq_extract_from_combination(
            product_tmpl_id, combination
        )

        (variant_ok, msg) = product_tmpl_id._cpq_ensure_valid_values(
            ptav_ids,
            custom_dict,
            raise_on_invalidity=False,
            validate_only=True,
        )

        return {
            "valid": variant_ok,
            "errors": msg,
        }

    @route("/cpq/<int:product_tmpl_id>/configure", type="json", auth="user")
    def cpq_configure(
        self,
        product_tmpl_id,
        combination,
    ):
        product_tmpl_id = request.env["product.template"].sudo().browse(product_tmpl_id)
        if not product_tmpl_id.cpq_ok:
            raise UserError(_("Not a CPQ enabled product!"))

        (ptav_ids, custom_dict) = self._cpq_extract_from_combination(
            product_tmpl_id, combination
        )

        variant_id = product_tmpl_id._cpq_get_create_variant(
            ptav_ids,
            custom_dict,
        )

        return {
            "product_tmpl_id": product_tmpl_id.id,
            "product_id": variant_id.id,
        }
