from markupsafe import Markup

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTicketMerge(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner1 = self.env["res.partner"].create(
            {
                "name": "Test Partner 1",
            }
        )
        self.partner2 = self.env["res.partner"].create(
            {
                "name": "Test Partner 2",
            }
        )
        ticket_model = self.env["helpdesk.ticket"]
        tag_model = self.env["helpdesk.tag"]
        self.tag1 = tag_model.create({"name": "Tag 1"})
        self.tag2 = tag_model.create({"name": "Tag 2"})
        self.ticket1 = ticket_model.create(
            {
                "name": "Ticket 1",
                "description": "Description of ticket 1",
                "priority": "3",
                "tag_ids": [(4, self.tag1.id, 0)],
                "partner_id": self.partner1.id,
            }
        )
        self.ticket2 = ticket_model.create(
            {
                "name": "Ticket 2",
                "description": "Description of ticket 2",
                "priority": "2",
                "tag_ids": [(4, self.tag2.id, 0)],
                "partner_id": self.partner1.id,
            }
        )
        self.ticket1.message_post(
            body="Initial message for ticket 1",
        )
        self.ticket2.message_post(
            body="Initial message for ticket 2",
        )
        self.ticket1.message_post(
            body="Extra message for ticket 1",
        )
        self.env["mail.activity"].create(
            {
                "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
                "note": "Follow up on ticket 2",
                "res_id": self.ticket2.id,
                "res_model": "helpdesk.ticket",
                "res_model_id": self.env.ref("helpdesk.model_helpdesk_ticket").id,
            }
        )
        self.env["ir.attachment"].create(
            {
                "name": "Test Attachment",
                "datas": "dGVzdCBkYXRh",  # Base64 encoded "test data"
                "res_model": "helpdesk.ticket",
                "res_id": self.ticket1.id,
                "mimetype": "text/plain",
            }
        )

    def test_merge_tickets(self):
        self.ticket1.merge_into(self.ticket2)

        # Check that ticket 1 is inactive
        self.assertFalse(self.ticket1.active)

        # Check that ticket 2 has the correct description
        expected_description = Markup(
            f"<p>Description of ticket 2</p>\n\n=== Merged from ticket {self.ticket1.id} (Ticket 1) ===\n\n<p>Description of ticket 1</p>"  # noqa: E501
        )  # noqa: E501
        self.assertEqual(self.ticket2.description, expected_description)

        # Check that messages were merged correctly
        messages = self.ticket2.message_ids.sorted("id")
        self.assertEqual(len(messages), 6)  # Includes the "Created" messages
        self.assertIn(
            "Initial message for ticket 1",
            messages[2].body,
        )
        self.assertIn(
            "Initial message for ticket 2",
            messages[3].body,
        )
        self.assertIn(
            "Extra message for ticket 1",
            messages[4].body,
        )

        # Check that attachments were moved
        attachments = self.env["ir.attachment"].search(
            [("res_model", "=", "helpdesk.ticket"), ("res_id", "=", self.ticket2.id)]
        )
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments.datas, b"dGVzdCBkYXRh")

        # Check that tags were merged correctly
        self.assertIn(self.tag1, self.ticket2.tag_ids)
        self.assertIn(self.tag2, self.ticket2.tag_ids)

        # Check that priority was updated
        self.assertEqual(self.ticket2.priority, "3")

        # Check that activities were merged correctly
        activities = self.ticket2.activity_ids
        self.assertEqual(len(activities), 1)

        # Check mail message forwarding
        self.ticket1.message_post(
            body="This is posted after the merge to ticket 2",
        )
        self.assertIn(
            "This is posted after the merge to ticket 2",
            self.ticket2.message_ids[0].body,
        )

    def test_merge_error(self):
        ticket3 = self.env["helpdesk.ticket"].create(
            {
                "name": "Ticket 2",
                "description": "Description of ticket 2",
                "partner_id": self.partner2.id,
            }
        )
        with self.assertRaises(ValueError):
            self.ticket1.merge_into(ticket3)
