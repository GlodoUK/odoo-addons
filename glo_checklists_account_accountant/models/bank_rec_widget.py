from odoo import api, models


class BenkRecWidget(models.Model):
    _inherit = "bank.rec.widget"

    @api.depends(
        "form_index",
        "state",
        "line_ids.account_id",
        "line_ids.date",
        "line_ids.name",
        "line_ids.partner_id",
        "line_ids.currency_id",
        "line_ids.amount_currency",
        "line_ids.balance",
        "line_ids.analytic_distribution",
        "line_ids.tax_repartition_line_id",
        "line_ids.tax_ids",
        "line_ids.tax_tag_ids",
        "line_ids.group_tax_id",
        "line_ids.reconcile_model_id",
    )
    def _compute_lines_widget(self):
        res = super()._compute_lines_widget()
        for line in self.lines_widget.get("lines", []):
            if "checklist_item_ids" in line:
                line["checklist_item_ids"] = {"value": []}
        return res
