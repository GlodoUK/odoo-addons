from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestHelpdeskTicketEscalate(TransactionCase):
    def setUp(self):
        super().setUp()

        self.team = self.env["helpdesk.team"].create(
            {
                "name": "Test Team",
            }
        )

        self.stage1 = self.env["helpdesk.stage"].create(
            {"name": "Test Stage", "team_ids": [(4, self.team.id)]}
        )

        self.ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "stage_id": self.stage1.id,
                "team_id": self.team.id,
            }
        )

    def test_helpdesk_ticket_escalate(self):
        self.ticket.action_toggle_escalated()

        self.assertTrue(
            self.ticket.is_escalated,
            "Ticket should be escalated",
        )

        self.ticket.action_toggle_escalated()

        self.assertFalse(
            self.ticket.is_escalated,
            "Ticket shouldn't be escalated",
        )
