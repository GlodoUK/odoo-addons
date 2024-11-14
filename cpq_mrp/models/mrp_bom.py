from odoo import _, api, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    @api.onchange("product_tmpl_id")
    def onchange_product_tmpl_id(self):
        res = super().onchange_product_tmpl_id()
        if not res:
            res = {}

            cpq_dynamic_bom_count = (
                self.env["cpq.dynamic.bom"]
                .sudo()
                .search_count([("product_tmpl_id", "=", self.product_tmpl_id.id)])
            )
            if cpq_dynamic_bom_count > 0:
                res["warning"] = {
                    "title": _("Configurable BoMs Exist"),
                    "message": _(
                        "There are already %d configurable BoMs for this product!"
                        " Attempting to use both standard BoMs and configurable"
                        " BoMs will result in inconsistent BoM handling!"
                    )
                    % cpq_dynamic_bom_count,
                }
        return res
