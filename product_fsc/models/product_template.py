from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    fsc_certified = fields.Boolean(string="FSC Certified", index=True)
    fsc_type_id = fields.Many2one("product_fsc.type", string="FSC Type")
    # Claims are fixed by FSC-STD-40-004.
    fsc_classification = fields.Selection(
        [
            ("fsc_100", "FSC 100%"),
            ("fsc_mix", "FSC Mix"),
            ("fsc_recycled", "FSC Recycled"),
            ("fsc_controlled_wood", "FSC Controlled Wood"),
        ],
        string="FSC Claim",
        index=True,
        help=(
            "FSC claim stated on sales and delivery documents:\n"
            "- FSC 100%: all material from FSC-certified forests.\n"
            "- FSC Mix: blend of certified, recycled and/or controlled wood "
            "(the certified/recycled share is given by the percentage).\n"
            "- FSC Recycled: made from reclaimed/recycled material.\n"
            "- FSC Controlled Wood: documents only, never on product labels."
        ),
    )
    # Mix and Recycled only. Stored as 0-1 for the percentage widget.
    fsc_percentage = fields.Float(
        string="FSC Certified Content",
        help="Share of FSC-certified / recycled content shown on the label.",
    )
    fsc_license_code = fields.Char(
        string="FSC Licence Code",
        help="FSC trademark licence code shown on the label, e.g. FSC® C123456.",
    )
    fsc_label = fields.Char(
        string="FSC Label",
        compute="_compute_fsc_label",
        store=True,
        help='Rendered FSC claim, e.g. "FSC Mix 70%".',
    )

    @api.depends("fsc_classification", "fsc_percentage")
    def _compute_fsc_label(self):
        labels = dict(
            self._fields["fsc_classification"]._description_selection(self.env)
        )
        for record in self:
            base = labels.get(record.fsc_classification)
            if not base:
                record.fsc_label = False
            elif (
                record.fsc_classification in ("fsc_mix", "fsc_recycled")
                and record.fsc_percentage
            ):
                record.fsc_label = f"{base} {record.fsc_percentage * 100:g}%"
            else:
                record.fsc_label = base

    @api.constrains("fsc_percentage")
    def _check_fsc_percentage(self):
        for record in self:
            if record.fsc_percentage and not 0 <= record.fsc_percentage <= 1:
                raise ValidationError(
                    self.env._("FSC certified content must be between 0 and 100%%.")
                )
