from odoo.addons.component.core import Component


class EdiMessageActionNoneComponent(Component):
    _name = "edi.message.action.none"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "action.none"
    _apply_on = "edi.message"

    def run_read(self, message_id, **kwargs):
        pass

    def run_write(self, message_id, **kwargs):
        pass
