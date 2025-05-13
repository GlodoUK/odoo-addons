from odoo.addons.component.core import Component

from ..exceptions import EdiException


class EdiMessageActionCodeComponent(Component):
    _name = "edi.message.action.code"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "action.code"
    _apply_on = "edi.message"

    def run_read(self, message_id, **kwargs):
        try:
            with self.env.cr.savepoint():
                self._safe_eval(
                    message_id.message_route_id.action_code, record=message_id
                )
        except (EdiException, ValueError) as e:
            # safe_eval usually raises as a ValueError, sadly
            raise EdiException(e) from e

    def run_write(self, route_id, **kwargs):
        kwargs.update({"route_id": route_id})
        try:
            with self.env.cr.savepoint():
                self._safe_eval(route_id.action_code, **kwargs)
        except (EdiException, ValueError) as e:
            # safe_eval usually raises as a ValueError, sadly
            raise EdiException(e) from e
