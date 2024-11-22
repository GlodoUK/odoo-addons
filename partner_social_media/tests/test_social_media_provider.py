from odoo.tests.common import TransactionCase


class TestSocialMediaProvider(TransactionCase):
    def setUp(self):
        super().setUp()
        self.social_media_provider = self.env[
            "res.partner.social.media.provider"
        ].create(
            {
                "name": "Test Social Media Provider",
                "url_format": "https://www.example.com/{account}",
                "font_awesome": "fa-test",
                "extract_regex": (
                    r"(https?://)?(www\.)?example.com/(?P<account>[a-zA-Z0-9_\-]+)"
                ),
            }
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

    def test_extract_from_url(self):
        (provider_id, account) = self.env[
            "res.partner.social.media.provider"
        ]._extract_provider_and_account_from_url("https://www.example.com/test123")

        self.assertEqual(
            account,
            "test123",
        )

        self.assertEqual(
            provider_id,
            self.social_media_provider,
        )

    def test_auto_extract_from_url(self):
        social_media_id = self.env["res.partner.social.media"].create(
            {
                "partner_id": self.partner.id,
                "website": "https://www.example.com/test123",
            }
        )

        self.assertEqual(
            social_media_id.account,
            "test123",
        )

        self.assertEqual(
            social_media_id.provider_id,
            self.social_media_provider,
        )

    def test_social_media_provider_url(self):
        social_media_id = self.env["res.partner.social.media"].create(
            {
                "partner_id": self.partner.id,
                "provider_id": self.social_media_provider.id,
                "account": "test123",
            }
        )

        self.assertEqual(
            social_media_id.website,
            "https://www.example.com/test123",
        )

        social_media_id.account = "test456"

        self.assertEqual(
            social_media_id.website,
            "https://www.example.com/test456",
        )

        social_media_id.account = False

        self.assertFalse(
            social_media_id.website,
        )

    def test_social_media_provider_link(self):
        social_media_id = self.env["res.partner.social.media"].create(
            {
                "partner_id": self.partner.id,
                "provider_id": self.social_media_provider.id,
                "account": "test123",
            }
        )

        self.assertEqual(
            social_media_id.link,
            '<a href="https://www.example.com/test123" target="_blank"><i'
            ' class="fa-test"></i> test123</a>',
        )

        social_media_id.account = "test456"

        self.assertEqual(
            social_media_id.link,
            '<a href="https://www.example.com/test456" target="_blank"><i'
            ' class="fa-test"></i> test456</a>',
        )

        social_media_id.account = False

        self.assertFalse(
            social_media_id.link,
        )
