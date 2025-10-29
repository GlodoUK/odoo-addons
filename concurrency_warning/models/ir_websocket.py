from odoo import models


class IrWebSocket(models.AbstractModel):
    _inherit = "ir.websocket"

    def _build_bus_channel_list(self, channels):
        res = super()._build_bus_channel_list(channels)
        if self.env.user._is_internal():
            res.append("poke")
        return res
