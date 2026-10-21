from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _crypt_context(self):
        # Allows import from other systems as-is.
        # Adding bcrypt allows Odoos to upgrade in-place.
        ctx = super()._crypt_context()
        ctx.update(schemes=["pbkdf2_sha512", "bcrypt", "plaintext"])
        return ctx
