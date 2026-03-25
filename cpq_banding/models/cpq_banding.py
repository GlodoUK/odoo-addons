from odoo import api, fields, models


class ProductBanding(models.Model):
    _name = "cpq.banding"
    _description = "CPQ Banding"
    _parent_name = "parent_id"
    _parent_store = True
    _order = "complete_name, id"
    _rec_name = "display_name"
    _rec_names_search = ["complete_name"]

    name = fields.Char(required=True)
    ref = fields.Char()
    complete_name = fields.Char(
        "Full Name",
        compute="_compute_complete_name",
        recursive=True,
        store=True,
        index="trigram",
    )
    parent_id = fields.Many2one(comodel_name="cpq.banding", ondelete="cascade")
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        comodel_name="cpq.banding",
        inverse_name="parent_id",
        string="Children",
        domain="[('parent_id', '=', False)]",
    )
    child_count = fields.Integer(compute="_compute_child_count")
    is_leaf = fields.Boolean(compute="_compute_is_leaf", store=True, index=True)
    comment = fields.Text()
    active = fields.Boolean(default=True)

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if "name" not in default:
            for banding, vals in zip(self, vals_list, strict=False):
                vals["name"] = self.env._("%s (copy)", banding.name)
        return vals_list

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

    @api.depends("child_ids")
    def _compute_child_count(self):
        for binding in self:
            if not binding.parent_path:
                binding.child_count = 0
                continue
            binding.child_count = (
                self.search_count(
                    [
                        ("parent_path", "=like", binding.parent_path + "%"),
                    ]
                )
                - 1
            )

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
