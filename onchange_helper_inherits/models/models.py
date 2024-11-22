from odoo import api, models


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def play_onchanges_inherits(self, vals, onchange_keys):
        # as-of https://github.com/OCA/server-tools/pull/2075
        # this is now a no-op.

        return self.play_onchanges(vals, onchange_keys)
