from odoo import fields, models


class MaintenanceEquipmentTemplate(models.Model):
    _name = "maintenance.equipment.template"
    _description = "Maintenance Equipment Template"

    active = fields.Boolean(
        default=True,
    )

    name = fields.Char(
        required=True,
    )

    sequence = fields.Integer(
        default=10,
    )

    description = fields.Html(
        required=True,
    )

    categ_count = fields.Integer(
        compute="_compute_categ_count",
        string="Categories",
    )

    equipment_count = fields.Integer(
        compute="_compute_equipment_count",
        string="Equipment",
    )

    def _compute_categ_count(self):
        data = self.env["maintenance.equipment.category"].read_group(
            [("template_id", "in", self.ids)],
            ["template_id"],
            ["template_id"],
        )

        mapped_data = dict(
            [(m["template_id"][0], m["template_id_count"]) for m in data]
        )

        for template in self:
            template.categ_count = mapped_data.get(template.id, 0)

    def _compute_equipment_count(self):
        data = self.env["maintenance.equipment"].read_group(
            [("template_id", "in", self.ids)],
            ["template_id"],
            ["template_id"],
        )

        mapped_data = dict(
            [(m["template_id"][0], m["template_id_count"]) for m in data]
        )

        for template in self:
            template.equipment_count = mapped_data.get(template.id, 0)
