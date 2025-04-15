import uuid

from werkzeug.urls import url_encode

from odoo.tests import HttpCase

PWD = "12345"


class TestWebsiteSaleRequireLogin(HttpCase):
    def setUp(self):
        self.website = self.env["website"].sudo().get_current_website()
        self.user = self.env["res.users"].create(
            {"name": str(uuid.uuid4()), "login": str(uuid.uuid4()), "password": PWD}
        )
        self.product = self.env["product.template"].create(
            {
                "name": str(uuid.uuid4()),
                "website_published": True,
            }
        )
        self.website_paths_to_check = ["/shop", self.product.website_url]

        return super().setUp()

    def test_no_auth_required_guest(self):
        self.website.ecommerce_requires_login = False
        self.authenticate(None, None)
        for path in self.website_paths_to_check:
            response = self.url_open(path, allow_redirects=False)
            self.assertEqual(
                response.status_code,
                200,
            )

    def test_auth_required_guest(self):
        self.authenticate(None, None)
        self.website.ecommerce_requires_login = True
        for path in self.website_paths_to_check:
            response = self.url_open(path, allow_redirects=False)
            self.assertEqual(
                response.status_code,
                int(self.website.ecommerce_requires_login_status_code),
            )
            qs = url_encode({"redirect": path})
            self.assertIn(f"/web/login?{qs}", response.headers["Location"])

    def test_auth_required_portal(self):
        self.website.ecommerce_requires_login = True
        self.authenticate("portal", "portal")
        for path in self.website_paths_to_check:
            response = self.url_open(path, allow_redirects=False)
            self.assertEqual(
                response.status_code,
                200,
            )

    def test_auth_required_guest_alt_status_code(self):
        self.authenticate(None, None)
        self.website.ecommerce_requires_login = True
        self.website.ecommerce_requires_login_status_code = "303"
        for path in self.website_paths_to_check:
            response = self.url_open(path, allow_redirects=False)
            self.assertEqual(
                response.status_code,
                303,
            )
            qs = url_encode({"redirect": path})
            self.assertIn(f"/web/login?{qs}", response.headers["Location"])
