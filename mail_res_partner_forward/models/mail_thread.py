from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_compute_recipients(self, message, msg_vals):
        recipient_data = super()._notify_compute_recipients(message, msg_vals)
        if not recipient_data:
            return recipient_data

        partner_dict = {x.get("id"): x for x in recipient_data}
        model_name = msg_vals.get("model") or message.sudo().model
        new_recipient_data = {}
        forwarded_history_data = []

        # for each partner being notified we check if it has a
        # forwarding_partner_id configured that is not being notified yet
        for partner in (
            self.env["res.partner"]
            .sudo()
            .with_context(prefetch_fields=["forwarding_rule_ids"])
            .search(
                [
                    ("id", "in", list(partner_dict.keys())),
                ]
            )
        ):
            forwarding_to_partner_id = partner._forwarding_to_partner(model_name)
            data = partner_dict[partner.id].copy()

            if partner != forwarding_to_partner_id:
                forwarded_history_data.append(
                    (
                        0,
                        0,
                        {
                            "replaced_partner_id": partner.id,
                            "partner_id": forwarding_to_partner_id.id,
                        },
                    )
                )

                data.update(
                    {
                        "id": forwarding_to_partner_id.id,
                        "share": forwarding_to_partner_id.partner_share,
                        "notif": (
                            forwarding_to_partner_id.user_ids
                            and forwarding_to_partner_id.user_ids[0].notification_type
                            or "email"
                        ),
                    }
                )

            new_recipient_data[forwarding_to_partner_id.id] = data

        if forwarded_history_data and message:
            message.sudo().write(
                {"forwarded_partner_history_ids": forwarded_history_data}
            )

        return list(new_recipient_data.values())
