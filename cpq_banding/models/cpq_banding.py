from odoo import api, fields, models


class CpqBanding(models.Model):
    _name = "cpq.banding"
    _description = "CPQ Banding"
    _parent_name = "parent_id"
    _parent_store = True
    _order = "complete_name, id"
    _rec_names_search = ["complete_name"]

    active = fields.Boolean(
        default=True,
    )

    name = fields.Char(
        required=True,
    )

    complete_name = fields.Char(
        "Full Name",
        compute="_compute_complete_name",
        recursive=True,
        store=True,
    )

    parent_path = fields.Char(
        index=True,
    )

    parent_id = fields.Many2one(
        "cpq.banding",
        ondelete="cascade",
    )

    is_leaf = fields.Boolean(
        compute="_compute_is_leaf",
        index=True,
        store=True,
    )

    ref = fields.Char(
        "Reference",
    )

    child_count = fields.Integer(
        compute="_compute_child_count",
    )

    child_ids = fields.One2many(
        "cpq.banding",
        "parent_id",
        "Children",
        domain="[('parent_id', '=', False)]",
    )

    comment = fields.Text()

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if "name" not in default:
            for banding, vals in zip(self, vals_list, strict=False):
                vals["name"] = self.env._("%s (copy)", banding.name)
        return vals_list

    def action_view_children(self):
        self.ensure_one()

        action = self.env["ir.actions.actions"]._for_xml_id(
            "cpq_banding.product_banding_action"
        )

        action["domain"] = [
            ("parent_path", "ilike", self.parent_path + "%"),
            ("id", "!=", self.id),
        ]

        action["name"] = self.env._("Children")

        return action

    @api.depends("child_ids")
    def _compute_child_count(self):
        for binding in self:
            binding.child_count = (
                self.search_count(
                    [
                        ("parent_path", "=like", binding.parent_path + "%"),
                    ]
                )
                - 1
            )

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for banding in self:
            if banding.parent_id:
                banding.complete_name = (
                    f"{banding.parent_id.complete_name}/{banding.name}"
                )
            else:
                banding.complete_name = banding.name

    @api.depends("name", "parent_id.complete_name")
    def _compute_display_name(self):
        res = super()._compute_display_name()
        for banding in self:
            banding.display_name = banding.complete_name
        return res

    @api.depends("child_ids")
    def _compute_is_leaf(self):
        read_group_data = self.env["cpq.banding"]._read_group(
            [("parent_id", "in", self.ids)],
            ["parent_id"],
        )

        parent_ids = {parent.id for (parent,) in read_group_data}

        for banding in self:
            banding.is_leaf = banding.id not in parent_ids

    # ruff: noqa: E501
    @api.model
    def _onchange_parent_id_warning(self):
        return [
            self.env._(
                "Changing the parent of a banding record may have unexpected results if this has been used on a product."
            ),
            self.env._(
                "The recommended action is to archive this banding and create a new one."
            ),
        ]

    @api.onchange("parent_id")
    def _onchange_parent_id(self):
        if self._origin and self._origin.parent_id != self.parent_id:
            return {
                "warning": {
                    "title": self.env._("Warning"),
                    "message": "\n".join(self._onchange_parent_id_warning()),
                }
            }
