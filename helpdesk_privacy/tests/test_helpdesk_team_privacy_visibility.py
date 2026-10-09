from odoo.tests import tagged

from .common import TestHelpdeskPrivacyCommon


@tagged("post_install", "-at_install")
class TestHelpdeskTeamPrivacyVisibility(TestHelpdeskPrivacyCommon):
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
