import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EdiSecret(models.Model):
    _name = "edi.secret"
    _description = "EDI Secret"
    _rec_name = "key"

    _sql_constraints = [
        (
            "backend_key_uniq",
            "unique (backend_id, key)",
            "Key must be unique per Backend!",
        )
    ]

    backend_id = fields.Many2one(
        "edi.backend",
        index=True,
        ondelete="cascade",
        required=True,
    )

    key = fields.Char(
        required=True,
    )

    value = fields.Char()

    @api.constrains("key")
    def _constrains_key(self):
        for secret in self:
            if not re.match(r"^[A-Z0-9_]*$", secret.key):
                msg = _("Key must be only contain characters A-Z, 0-9 and _")
                raise ValidationError(msg)
