from odoo.addons.helpdesk.tests.test_helpdesk_team_privacy_visibility import (
    TestHelpdeskTeamPrivacyVisibility,
)
from odoo.addons.mail.tests.common import mail_new_test_user


class TestHelpdeskTeamPrivacyVisibility(TestHelpdeskTeamPrivacyVisibility):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.portal_user_a = mail_new_test_user(
            cls.env,
            name="helpdesk_portal_a",
            login="helpdesk_portal_a",
            email="helpdesk_a@portal.com",
            notification_type="email",
            groups="base.group_portal",
        )

        cls.portal_user_b = mail_new_test_user(
            cls.env,
            name="helpdesk_portal_b",
            login="helpdesk_portal_b",
            email="helpdesk_b@portal.com",
            notification_type="email",
            groups="base.group_portal",
        )

        cls.portal_user_a.partner_id.commercial_partner_id = cls.partner.id
        cls.portal_user_b.partner_id.commercial_partner_id = cls.partner.id

    def test_helpdesk_team_visibility_private(self):
        self.ticket.write({"partner_id": self.partner.id})

        # Company Visible Ticket.
        # User A should be able to view the helpdesk ticket.
        # User B should be able to view the helpdesk ticket.
        self.assertTrue(self.search_test_ticket_with_user(self.portal_user_a))
        self.assertTrue(self.search_test_ticket_with_user(self.portal_user_b))

        self.ticket.write({"is_private": True})

        # Private Ticket.
        # User A should not be able to view the helpdesk ticket.
        # User B should not be able to view the helpdesk ticket.
        self.assertFalse(self.search_test_ticket_with_user(self.portal_user_a))
        self.assertFalse(self.search_test_ticket_with_user(self.portal_user_b))

        self.ticket.message_subscribe(self.portal_user_a.partner_id.ids)

        # Private Ticket.
        # User A is subscribed and should be able to view the helpdesk ticket.
        # User B should not be able to view the helpdesk ticket.
        self.assertTrue(self.search_test_ticket_with_user(self.portal_user_a))
        self.assertFalse(self.search_test_ticket_with_user(self.portal_user_b))

        self.ticket.message_subscribe(self.portal_user_b.partner_id.ids)

        # Private Ticket.
        # User A is subscribed and should be able to view the helpdesk ticket.
        # User B is subscribed and should be able to view the helpdesk ticket.
        self.assertTrue(self.search_test_ticket_with_user(self.portal_user_a))
        self.assertTrue(self.search_test_ticket_with_user(self.portal_user_b))
