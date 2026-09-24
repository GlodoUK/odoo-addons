from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestActivityFeed(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.partner"].create(
            {"name": "Feed Test Co", "is_company": True}
        )
        cls.contact = cls.env["res.partner"].create(
            {"name": "Feed Test Contact", "parent_id": cls.company.id}
        )

    def _post(self, partner, body, **kwargs):
        return partner.message_post(
            body=body,
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            **kwargs,
        )

    def _message(self, partner, **values):
        return self.env["mail.message"].create(
            {
                "model": "res.partner",
                "res_id": partner.id,
                "message_type": "notification",
                "body": "",
                **values,
            }
        )

    def _feed(self, partner):
        action = partner.action_activity_feed()
        return self.env["mail.message"].search(action["domain"])

    def test_comment_included(self):
        message = self._post(self.company, "<p>Called about the order</p>")
        self.assertIn(message, self._feed(self.company))

    def test_tracking_message_excluded(self):
        field = self.env["ir.model.fields"]._get("res.partner", "name")
        message = self._message(
            self.company,
            body="<p>Name changed</p>",
            tracking_value_ids=[
                Command.create(
                    {
                        "field_id": field.id,
                        "old_value_char": "Before",
                        "new_value_char": "After",
                    }
                )
            ],
        )
        self.assertNotIn(message, self._feed(self.company))

    def test_blank_body_excluded(self):
        for body in ("", "<p><br></p>", "<p></p>"):
            message = self._message(self.company, body=body)
            self.assertNotIn(
                message,
                self._feed(self.company),
                f"blank body {body!r} should be excluded",
            )

    def test_attachment_only_included(self):
        attachment = self.env["ir.attachment"].create(
            {
                "name": "quote.pdf",
                "raw": b"pdf-bytes",
                "res_model": "res.partner",
                "res_id": self.company.id,
            }
        )
        message = self._message(
            self.company,
            body="",
            attachment_ids=[Command.set(attachment.ids)],
        )
        self.assertIn(message, self._feed(self.company))

    def test_creation_log_notes_excluded(self):
        # models without a creation subtype: plain _message_log note
        log = self.company._message_log(body="Contact created")
        self.assertNotIn(log, self._feed(self.company))
        # models with a creation subtype: marker div around the body
        marked = self._post(
            self.company,
            '<div summary="o_mail_notification"><p>Contact created</p></div>',
        )
        self.assertNotIn(marked, self._feed(self.company))
        # but a human "Log note" from the chatter survives
        note = self.company.message_post(
            body="<p>Human-logged note</p>",
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )
        self.assertIn(note, self._feed(self.company))

    def test_user_notification_excluded(self):
        message = self._message(
            self.company,
            body="<p>You have been assigned</p>",
            message_type="user_notification",
        )
        self.assertNotIn(message, self._feed(self.company))

    def test_child_contact_rolls_up_to_company(self):
        on_contact = self._post(self.contact, "<p>Spoke to the contact</p>")
        on_company = self._post(self.company, "<p>Spoke to the company</p>")
        feed = self._feed(self.company)
        self.assertIn(on_contact, feed)
        self.assertIn(on_company, feed)

    def test_contact_action_resolves_to_commercial_partner(self):
        on_company = self._post(self.company, "<p>Spoke to the company</p>")
        contact_feed = self._feed(self.contact)
        self.assertIn(on_company, contact_feed)
        action = self.contact.action_activity_feed()
        self.assertIn(self.company.display_name, action["name"])

    def test_speculative_document_source(self):
        if "sale.order" not in self.env:
            self.skipTest("sale is not installed")
        order = self.env["sale.order"].create({"partner_id": self.contact.id})
        message = order.message_post(
            body="<p>Discussed the quote</p>",
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )
        self.assertIn(message, self._feed(self.company))

    def test_event_subtype_included_despite_tracking(self):
        subtype = self.env.ref("sale.mt_order_confirmed", raise_if_not_found=False)
        if not subtype:
            self.skipTest("sale is not installed")
        order = self.env["sale.order"].create({"partner_id": self.company.id})
        field = self.env["ir.model.fields"]._get("sale.order", "state")
        message = self.env["mail.message"].create(
            {
                "model": "sale.order",
                "res_id": order.id,
                "message_type": "notification",
                "subtype_id": subtype.id,
                "body": "",
                "tracking_value_ids": [
                    Command.create(
                        {
                            "field_id": field.id,
                            "old_value_char": "Quotation",
                            "new_value_char": "Sales Order",
                        }
                    )
                ],
            }
        )
        self.assertIn(message, self._feed(self.company))

    def test_activity_feed_summary(self):
        if "sale.order" not in self.env:
            self.skipTest("sale is not installed")
        from odoo.tools.misc import formatLang

        order = self.env["sale.order"].create({"partner_id": self.company.id})
        message = order.message_post(
            body="<p>Quote discussion</p>",
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )
        self.assertEqual(
            message.activity_feed_summary,
            formatLang(self.env, order.amount_total, currency_obj=order.currency_id),
        )
        partner_message = self._post(self.company, "<p>No summary here</p>")
        self.assertFalse(partner_message.activity_feed_summary)

    def test_is_commercial_partner(self):
        self.assertTrue(self.company.is_commercial_partner)
        self.assertFalse(self.contact.is_commercial_partner)

    def test_activity_feed_is_note(self):
        note = self.company.message_post(
            body="<p>Internal remark</p>",
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )
        comment = self._post(self.company, "<p>Public reply</p>")
        self.assertTrue(note.activity_feed_is_note)
        self.assertFalse(comment.activity_feed_is_note)
