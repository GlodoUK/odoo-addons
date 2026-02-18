from odoo.tests import tagged

from .common import TestHelpdeskPrivacyCommon


@tagged("post_install", "-at_install")
class TestMessageSubscribe(TestHelpdeskPrivacyCommon):
    def test_private_ticket_message_subscribe(self):
        ticket_id = self.env["helpdesk.ticket"].create(
            {
                "partner_id": self.portal_user_a.partner_id.id,
                "name": "Test portal user a's private ticket",
                "is_private": True,
            }
        )

        self.assertTrue(self.portal_user_a.partner_id in ticket_id.message_partner_ids)
        self.assertTrue(
            self.portal_user_b.partner_id not in ticket_id.message_partner_ids
        )

        ticket_id.with_context(
            helpdesk_privacy_only_subscribe_existing_partners=True
        )._message_subscribe(partner_ids=self.portal_user_b.partner_id.ids)

        self.assertTrue(
            self.portal_user_b.partner_id not in ticket_id.message_partner_ids
        )

    def test_public_ticket_message_subscribe(self):
        ticket_id = self.env["helpdesk.ticket"].create(
            {
                "partner_id": self.portal_user_a.partner_id.id,
                "name": "Test portal user a's public ticket",
                "is_private": False,
            }
        )

        self.assertTrue(self.portal_user_a.partner_id in ticket_id.message_partner_ids)
        self.assertTrue(
            self.portal_user_b.partner_id not in ticket_id.message_partner_ids
        )

        ticket_id._message_subscribe(partner_ids=self.portal_user_b.partner_id.ids)

        self.assertTrue(self.portal_user_b.partner_id in ticket_id.message_partner_ids)
