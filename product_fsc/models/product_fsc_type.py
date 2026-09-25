from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductFscType(models.Model):
    _name = "product_fsc.type"
    _description = "FSC Type"
    _parent_store = True
    # Codes don't sort as text (W10 < W2).
    _order = "sequence, code, id"
    _rec_names_search = ["name", "code"]

    # V3-0 reuses V2-1 codes with new meanings.
    _standard_code_uniq = models.Constraint(
        "unique (standard, code)",
        "An FSC type with the same code already exists for this standard.",
    )

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    standard = fields.Selection(
        [("fsc_std_40_004a_v2_1", "FSC-STD-40-004a V2-1")],
        required=True,
        default="fsc_std_40_004a_v2_1",
        index=True,
    )
    parent_id = fields.Many2one(
        comodel_name="product_fsc.type",
        string="Parent Type",
        index=True,
        ondelete="restrict",
        domain="[('standard', '=', standard)]",
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        comodel_name="product_fsc.type",
        inverse_name="parent_id",
        string="Child Types",
    )

    @api.depends("name", "code")
    def _compute_display_name(self):
        for record in self:
            record.display_name = (
                f"[{record.code}] {record.name}" if record.code else record.name
            )

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if self._has_cycle():
            raise ValidationError(self.env._("You cannot create recursive FSC types."))

    @api.constrains("parent_id", "standard")
    def _check_parent_standard(self):
        for record in self | self.child_ids:
            if record.parent_id and record.parent_id.standard != record.standard:
                raise ValidationError(
                    self.env._(
                        "FSC type %(type)s must belong to the same standard as "
                        "its parent %(parent)s.",
                        type=record.display_name,
                        parent=record.parent_id.display_name,
                    )
                )
