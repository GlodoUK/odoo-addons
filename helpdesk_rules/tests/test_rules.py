from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRules(TransactionCase):
    def setUp(self):
        super().setUp()

        self.team_id = self.env["helpdesk.team"].create({"name": "Test Team"})

    def test_no_rules(self):
        ticket_id = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "team_id": self.team_id.id,
            }
        )
        self.assertTrue(ticket_id.active, "Ticket should not be archived")

    def test_archive(self):
        self.team_id.write(
            {
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Auto-Archive ALL new tickets",
                            "trigger": "on_create",
                            "action": "archive",
                            "domain": "[]",
                        },
                    ),
                ],
            }
        )

        ticket_id = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "team_id": self.team_id.id,
            }
        )

        self.assertTrue(not ticket_id.active, "Ticket should be archived")

    def test_multiple_rules(self):
        self.team_id.write(
            {
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Auto-Archive ALL new P3 tickets",
                            "trigger": "on_create",
                            "action": "archive",
                            "domain": "[('priority', '=', '3')]",
                            "stop": True,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Move ALL new P2 tickets to P1",
                            "trigger": "on_create",
                            "action": "code",
                            "domain": "[('priority', '=', '2')]",
                            "code": "record.write({ 'priority': '1' })",
                            "stop": True,
                        },
                    ),
                ],
            }
        )

        non_matching_ticket_id = self.env["helpdesk.ticket"].create(
            {"name": "Test Ticket", "team_id": self.team_id.id, "priority": False}
        )

        self.assertTrue(non_matching_ticket_id.active, "Ticket should not be archived")
        self.assertTrue(
            not non_matching_ticket_id.priority,
            "Ticket priority should stay the same",
        )

        p3_ticket_id = self.env["helpdesk.ticket"].create(
            {"name": "Test Ticket", "team_id": self.team_id.id, "priority": "3"}
        )

        self.assertTrue(not p3_ticket_id.active, "Ticket should be archived")
        self.assertTrue(p3_ticket_id.priority == "3", "Ticket should stay the same")

        p2_ticket_id = self.env["helpdesk.ticket"].create(
            {"name": "Test Ticket", "team_id": self.team_id.id, "priority": "2"}
        )

        self.assertTrue(p2_ticket_id.active, "Ticket should not be archived")
        self.assertTrue(p2_ticket_id.priority == "1", "Ticket should be moved to p1")
