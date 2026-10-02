from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain

# Context key that switches a widget (and only that widget) over to showing the
# full hierarchy path instead of the plain partner name.
SHOW_PATH = "hierarchy_show_path"


class ResPartner(models.Model):
    _inherit = "res.partner"

    hierarchy_parent_id = fields.Many2one(
        "res.partner",
        index=True,
        ondelete="set null",
    )
    hierarchy_child_ids = fields.One2many(
        "res.partner",
        "hierarchy_parent_id",
    )
    hierarchy_type_id = fields.Many2one(
        "res.partner.hierarchy.type",
        ondelete="restrict",
        index="btree_not_null",
        help="How this partner relates to its hierarchy parent.",
    )
    hierarchy_complete_name = fields.Char(
        string="Hierarchy Path",
        compute="_compute_hierarchy_complete_name",
        recursive=True,
        store=True,
        index="btree_not_null",
    )
    hierarchy_root_id = fields.Many2one(
        "res.partner",
        compute="_compute_hierarchy_root_id",
        recursive=True,
        store=True,
        index=True,
        help="Top-most partner of the hierarchy, for grouping and reporting.",
    )
    hierarchy_child_count = fields.Integer(compute="_compute_hierarchy_child_count")

    @api.depends("complete_name", "hierarchy_parent_id.hierarchy_complete_name")
    def _compute_hierarchy_complete_name(self):
        for partner in self:
            if partner.hierarchy_parent_id:
                partner.hierarchy_complete_name = (
                    f"{partner.hierarchy_parent_id.hierarchy_complete_name}"
                    " / "
                    f"{partner.complete_name}"
                )
            else:
                partner.hierarchy_complete_name = partner.complete_name

    @api.depends("hierarchy_parent_id.hierarchy_root_id")
    def _compute_hierarchy_root_id(self):
        for partner in self:
            partner.hierarchy_root_id = (
                partner.hierarchy_parent_id.hierarchy_root_id or partner
            )

    def _compute_hierarchy_child_count(self):
        counts = dict(
            self.env["res.partner"]._read_group(
                [("hierarchy_parent_id", "in", self.ids)],
                ["hierarchy_parent_id"],
                ["__count"],
            )
        )
        for partner in self:
            partner.hierarchy_child_count = counts.get(partner, 0)

    def write(self, vals):
        # A type without a link is meaningless, and would quietly skew any report
        # grouped on it. Drop it with the link rather than constraining the user.
        if "hierarchy_parent_id" in vals and not vals["hierarchy_parent_id"]:
            vals = dict(vals, hierarchy_type_id=False)
        return super().write(vals)

    @api.constrains("hierarchy_parent_id")
    def _check_hierarchy_parent_id(self):
        if self._has_cycle("hierarchy_parent_id"):
            raise ValidationError(
                self.env._("You cannot create a recursive partner hierarchy.")
            )

    @api.depends("hierarchy_parent_id.hierarchy_complete_name")
    @api.depends_context(SHOW_PATH)
    def _compute_display_name(self):
        super()._compute_display_name()
        if not self.env.context.get(SHOW_PATH):
            return
        for partner in self:
            if partner.hierarchy_parent_id:
                partner.display_name = (
                    f"{partner.hierarchy_parent_id.hierarchy_complete_name}"
                    f" / {partner.display_name}"
                )

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        if not self.env.context.get(SHOW_PATH):
            return domain
        if not value or not operator.endswith("like") or operator.startswith("not"):
            return domain
        # Typing an ancestor's name should find its descendants too.
        return Domain.OR([domain, Domain("hierarchy_complete_name", operator, value)])

    def action_open_hierarchy_children(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Hierarchy Children"),
            "res_model": "res.partner",
            "view_mode": "list,form",
            "domain": [("hierarchy_parent_id", "=", self.id)],
            "context": {"default_hierarchy_parent_id": self.id},
        }
