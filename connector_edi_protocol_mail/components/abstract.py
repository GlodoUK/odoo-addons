import email

from odoo.tools.safe_eval import wrap_module

from odoo.addons.component.core import AbstractComponent


class AbstractEdiComponent(AbstractComponent):
    _inherit = "edi.connector"

    def _get_default_eval_context(self):
        res = super()._get_default_eval_context()

        res.update(
            {
                "email": wrap_module(
                    email,
                    {
                        "message": email.message.__all__,
                        "parser": email.parser.__all__,
                        "policy": email.policy.__all__,
                        "generator": email.generator.__all__,
                    },
                )
            }
        )

        return res
