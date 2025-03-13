from odoo.http import request

from odoo.addons.portal.controllers import portal


class CustomerPortal(portal.CustomerPortal):
    def _float_to_time(self, inc_float):
        """Format a float: used to display integral or fractional values as
        human-readable time spans (e.g. 1.5 as "01:30").
        """
        if isinstance(inc_float, float):
            hours, minutes = divmod(abs(inc_float) * 60, 60)
            minutes = round(minutes)
            if minutes == 60:
                minutes = 0
                hours += 1
            if inc_float < 0:
                return "-%02d:%02d" % (hours, minutes)
            return "%02d:%02d" % (hours, minutes)
        return False

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        if (
            request.env.user.partner_id
            and request.env.user.partner_id.balance_partner_id
        ):
            request.env.user.partner_id._compute_balance_partner_id()
            balance_partner_id = request.env.user.partner_id.balance_partner_id
            time_balance_dict = {}
            for (
                partner_time_balance_id
            ) in balance_partner_id.glo_partner_time_balance_ids:
                res_time = self._float_to_time(partner_time_balance_id.time_balance)
                if res_time:
                    time_balance_dict[
                        partner_time_balance_id.product_id.name
                    ] = res_time
            values.update(
                {
                    "sum_balance": self._float_to_time(
                        balance_partner_id.glo_sum_time_balance
                    ),
                    "balance_items": time_balance_dict,
                }
            )
        return values
