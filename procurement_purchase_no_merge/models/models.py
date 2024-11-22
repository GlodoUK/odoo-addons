from odoo import _, api, fields, models  # noqa


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _make_po_get_domain(self, values, partner):
        domain = super(StockRule, self)._make_po_get_domain(values, partner)
        if (
            not partner.property_supplier_consolidation or
            partner.property_supplier_consolidation == "consolidate"
        ):
            return domain

        group_id = values.get("group_id")

        if not group_id or not group_id.sale_id:
            return domain

        domain += (
            ("order_line.move_dest_ids.group_id.sale_id", "=", group_id.sale_id.id),
        )
        return domain


class ResPartner(models.Model):
    _inherit = "res.partner"

    property_supplier_consolidation = fields.Selection(
        [
            ("separate", "Separate"),
            ("consolidate", "Consolidate")
        ],
        default="separate",
        string="RFQ Consolidation",
        help="""
        Controls how Purchase Orders automatically raised from a Sale Order are
        created.
        By default Odoo will merge many POs together.

        * Separate - Treat each SO as a unique PO, prevent merging
        * Consolidate - Default odoo behaviour, where many POs may be
          automatically merged
        """
    )
