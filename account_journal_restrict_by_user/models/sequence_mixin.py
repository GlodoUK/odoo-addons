from odoo import models


class SequenceMixin(models.AbstractModel):
    _inherit = "sequence.mixin"

    def _get_last_sequence(self, relaxed=False, lock=True):
        return super(SequenceMixin, self.sudo())._get_last_sequence(
            relaxed=relaxed, lock=lock
        )
