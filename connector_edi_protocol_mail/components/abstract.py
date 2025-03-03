import email

from odoo.addons.component.core import AbstractComponent


class AbstractEdiComponent(AbstractComponent):
    _inherit = "edi.connector"

    def _get_default_eval_context(self):
        res = super()._get_default_eval_context()

        res.update({"email": email})

        return res
