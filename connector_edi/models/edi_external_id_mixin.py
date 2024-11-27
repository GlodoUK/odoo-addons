from odoo import fields, models


class EdiExternalIdWarningMixin(models.AbstractModel):
    """
    Utility methods and fields to warn users against editing records where there
    something is defined by XML and noupdate=0
    """

    _name = "edi.external_id.warning.mixin"
    _description = "Abstract EDI External ID Warning Mixin"

    warn_external_id_updateable = fields.Boolean(
        compute="_compute_warn_external_id_updateable",
        search="_search_warn_external_id_updateable",
        string="Updateable External ID",
    )

    def _compute_warn_external_id_updateable(self):
        data = (
            self.env["ir.model.data"]
            .sudo()
            .search_read(
                [
                    ("model", "=", self._name),
                    ("res_id", "in", self.ids),
                ],
                ["res_id", "noupdate"],
                order="id",
            )
        )

        data_dict = {i["res_id"]: i for i in data}

        for record in self:
            record.warn_external_id_updateable = not (
                data_dict.get(record.id, {}).get("noupdate", True)
            )

    def _search_warn_external_id_updateable(self, operator, operand):
        data = (
            self.env["ir.model.data"]
            .sudo()
            .search_read(
                [
                    ("model", "=", self._name),
                    ("noupdate", operator, not operand),
                ],
                ["res_id"],
                order="id",
            )
        )

        ids = [i["res_id"] for i in data]

        return [("id", "in", ids)]
