from odoo import _, api, fields, models


class ProductConformityAlert(models.Model):
    _name = "product.conformity.alert"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Product Conformity Alert"
    _order = "id DESC"

    name = fields.Char(
        copy=False,
        default=lambda self: _("New"),
        required=True,
    )

    product_id = fields.Many2one(
        "product.product",
        required=True,
    )

    product_tmpl_id = fields.Many2one(
        "product.template",
        related="product_id.product_tmpl_id",
        store=True,
    )

    date_acknowledge = fields.Datetime(
        tracking=True,
    )

    date_end = fields.Datetime(
        required=True,
        tracking=True,
    )

    date_start = fields.Datetime(
        default=fields.Datetime.now,
        required=True,
        tracking=True,
    )

    reason = fields.Selection(
        [
            ("quantity", "Conformity Quantity Exceeded"),
            ("time", "Conformity Period Expired"),
        ],
    )

    state = fields.Selection(
        [
            ("open", "Open"),
            ("pass", "Pass"),
            ("fail", "Fail"),
            ("suppress", "Suppress"),
        ],
        default="open",
        required=True,
        tracking=True,
    )

    bom_count = fields.Integer(
        compute="_compute_bom_count",
    )

    mrp_production_ids = fields.Many2many(
        "mrp.production",
    )

    mrp_production_count = fields.Integer(
        compute="_compute_mrp_production_count",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "product.conformity"
                ) or _("New")
        return super().create(vals_list)

    @api.depends("product_id")
    def _compute_bom_count(self):
        for alert in self:
            alert.bom_count = self.env["mrp.bom"].search_count(
                [
                    "|",
                    ("product_id", "=", alert.product_id.id),
                    "&",
                    ("product_id", "=", False),
                    ("product_tmpl_id", "=", alert.product_tmpl_id.id),
                ]
            )

    @api.depends("mrp_production_count")
    def _compute_mrp_production_count(self):
        for alert in self:
            alert.mrp_production_count = len(alert.mrp_production_ids)

    def action_fail(self):
        self.write({"date_acknowledge": fields.Datetime.now(), "state": "fail"})

    def action_pass(self):
        self.write({"date_acknowledge": fields.Datetime.now(), "state": "pass"})

    def action_suppress(self):
        self.write({"date_acknowledge": fields.Datetime.now(), "state": "suppress"})

    def action_view_boms(self):
        self.ensure_one()

        domain = [
            "|",
            ("product_id", "=", self.product_id.id),
            "&",
            ("product_id", "=", False),
            ("product_tmpl_id", "=", self.product_tmpl_id.id),
        ]

        action = {
            "name": _("Bills of Materials"),
            "res_model": "mrp.bom",
            "type": "ir.actions.act_window",
            "domain": domain,
            "view_mode": "tree,form",
        }

        bom_ids = self.env["mrp.bom"].search(domain)

        if len(bom_ids) == 1:
            action.update(
                {
                    "res_id": bom_ids.id,
                    "view_mode": "form",
                }
            )

        return action

    def action_view_mrp_productions(self):
        self.ensure_one()

        action = {
            "res_model": "mrp.production",
            "type": "ir.actions.act_window",
        }

        if len(self.mrp_production_ids) == 1:
            action.update(
                {
                    "name": _("Productions"),
                    "res_id": self.mrp_production_ids.id,
                    "view_mode": "form",
                }
            )

        else:
            action.update(
                {
                    "domain": [("id", "in", self.mrp_production_ids.ids)],
                    "view_mode": "tree,form",
                }
            )

        return action
