from email.message import EmailMessage

from odoo.tests import TransactionCase

DEFAULT_MARKER = "is used to collect replies and should not be used to directly contact"


class TestCustomMessage(TransactionCase):
    def setUp(self):
        super().setUp()

        self.company_id = self.env["res.company"].create(
            {
                "name": "Test Company A",
            }
        )

    def _render_mail_bounce_catchall(self):
        msg = EmailMessage()

        # Set headers
        msg["From"] = "alice@example.com"
        msg["To"] = "bob@example.net"
        msg["Subject"] = "Test Message"
        msg["Date"] = "Fri, 13 Jun 2025 10:00:00 -0000"
        msg["Message-ID"] = "<fake-message-id@example.com>"

        body = (
            self.env["ir.qweb"]
            .with_company(self.company_id)
            ._render(
                "mail.mail_bounce_catchall",
                {
                    "message": msg,
                },
            )
        )

        return body

    def test_no_custom_message(self):
        self.assertFalse(self.company_id.use_custom_catchall_bounce_message)
        body = self._render_mail_bounce_catchall()
        self.assertTrue(DEFAULT_MARKER in body)

    def test_custom_message_plaintext(self):
        self.company_id.use_custom_catchall_bounce_message = True
        self.assertTrue(self.company_id.use_custom_catchall_bounce_message)
        self.company_id.custom_catchall_bounce_message = "TEST123456"
        body = self._render_mail_bounce_catchall()
        self.assertTrue(DEFAULT_MARKER not in body)
        self.assertTrue("TEST123456" in body)

    def test_custom_message_html(self):
        self.company_id.use_custom_catchall_bounce_message = True
        self.assertTrue(self.company_id.use_custom_catchall_bounce_message)
        self.company_id.custom_catchall_bounce_message = "<ul><li>ONE</li></ul>"
        body = self._render_mail_bounce_catchall()
        self.assertTrue(DEFAULT_MARKER not in body)
        self.assertTrue(self.company_id.custom_catchall_bounce_message in body)
