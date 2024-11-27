import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EdiSecret(models.Model):
    _name = "edi.secret"
    _description = "EDI Secret"
    _rec_name = "key"

    backend_id = fields.Many2one(
        "edi.backend",
        required=True,
        index=True,
        ondelete="cascade",
    )
    key = fields.Char("Key", required=True)
    value = fields.Char("Value")

    @api.constrains("key")
    def _constrains_key(self):
        for r in self:
            if not re.match(r"^[A-Z0-9_]*$", r.key):
                raise ValidationError(
                    _("Key must be only contain the characters A-Z, 0-9")
                )

    _sql_constraints = [
        ("backend_key_uniq", "unique (backend_id, key)", "Key must be unique.")
    ]
