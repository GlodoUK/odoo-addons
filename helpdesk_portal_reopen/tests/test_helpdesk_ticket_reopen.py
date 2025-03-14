from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestHelpdeskTicketReopen(TransactionCase):
    def setUp(self):
        super().setUp()
        self.team = self.env["helpdesk.team"].create(
            {"name": "Test Team", "allow_portal_ticket_reopen": True}
        )
        self.assignee = self.env["res.users"].create(
            {"name": "Test User", "login": "test", "email": "testassignee@example.com"}
        )
        self.stage = self.env["helpdesk.stage"].create(
            {"name": "Test Stage", "team_ids": [(4, self.team.id)]}
        )
        self.stage2 = self.env["helpdesk.stage"].create(
            {"name": "Test Done Stage", "team_ids": [(4, self.team.id)], "fold": True}
        )
        self.team.reopen_ticket_stage = self.stage.id
        self.ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "team_id": self.team.id,
                "stage_id": self.stage2.id,
                "closed_by_partner": True,
            }
        )

    def test_ticket_reopen(self):
        self.ticket.reopen()
        self.assertNotEqual(self.ticket.stage_id, self.stage2, "Ticket didn't reopen")
        self.assertEqual(
            self.ticket.stage_id, self.stage, "Ticket in wrong stage after reopen"
        )
        self.assertFalse(
            self.ticket.closed_by_partner, "Ticket should not be closed by partner"
        )

    def test_ticket_unassign(self):
        self.team.clear_assigned_on_reopen = True
        self.ticket.reopen()
        self.assertFalse(self.ticket.user_id, "Ticket should not be assigned")
