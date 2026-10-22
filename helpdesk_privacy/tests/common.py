from odoo.addons.helpdesk.tests.test_helpdesk_team_privacy_visibility import (
    TestHelpdeskTeamPrivacyVisibility,
)
from odoo.addons.mail.tests.common import mail_new_test_user


class TestHelpdeskPrivacyCommon(TestHelpdeskTeamPrivacyVisibility):
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
