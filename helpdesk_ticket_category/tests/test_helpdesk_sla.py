from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class HelpdeskSLA(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.helpdesk_team = cls.env["helpdesk.team"].create(
            {
                "name": "Test Team SLA Reached",
                "use_sla": True,
            }
        )

        cls.stage_new = cls.env["helpdesk.stage"].create(
            {
                "name": "New",
                "sequence": 10,
                "team_ids": [(6, 0, cls.helpdesk_team.ids)],
            }
        )

        cls.stage_progress = cls.env["helpdesk.stage"].create(
            {
                "name": "In Progress",
                "sequence": 20,
                "team_ids": [(6, 0, cls.helpdesk_team.ids)],
            }
        )

        cls.categ_question = cls.env["helpdesk.ticket.category"].create(
            {
                "name": "Question_Test",
            }
        )

        cls.categ_issue = cls.env["helpdesk.ticket.category"].create(
            {
                "name": "Issue_Test",
            }
        )

        cls.sla = cls.env["helpdesk.sla"].create(
            {
                "name": "SLA",
                "team_id": cls.helpdesk_team.id,
                "ticket_categ_ids": [(6, 0, cls.categ_question.ids)],
                "time": 32,
            }
        )

    def test_sla_ticket_categ(self):
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Name",
                "team_id": self.helpdesk_team.id,
                "ticket_categ_id": self.categ_issue.id,
            }
        )

        self.assertFalse(
            ticket.sla_status_ids,
            "SLA should not have been applied yet",
        )

        ticket.ticket_categ_id = self.categ_question

        self.assertEqual(
            ticket.sla_status_ids.sla_id,
            self.sla,
            "SLA should have been applied",
        )
