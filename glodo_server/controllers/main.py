"""
Glodo Cloud Server Controllers.

Handles become redirects to client instances.
"""

import json
import logging
import time

from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class GlodoCloudServer(http.Controller):
    """
    Controller endpoints for Glodo Cloud server functionality.
    """

    @http.route(
        "/glodo_cloud/ping",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    def glodo_cloud_ping(self, **kwargs):
        """Simple ping endpoint for connectivity testing."""
        return request.make_response(
            json.dumps({"status": "ok", "timestamp": int(time.time())}),
            headers=[("Content-Type", "application/json")],
        )

    @http.route(
        "/glodo_cloud/become_redirect",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def glodo_cloud_become_redirect(self, database_id=None, user_id=None, **kwargs):
        """
        Redirect endpoint that creates an encrypted become request and redirects
        the admin to the client instance.

        This is an intermediate endpoint that:
        1. Validates the admin has access
        2. Creates a fresh encrypted payload with current timestamp
        3. Builds a form that POSTs to the client's become endpoint

        Args:
            database_id: ID of the glodo.instance.database record
            user_id: ID of the glodo.remote.user record
        """
        if not database_id or not user_id:
            raise BadRequest("Missing database_id or user_id")

        try:
            database_id = int(database_id)
            user_id = int(user_id)
        except (TypeError, ValueError) as e:
            raise BadRequest("Invalid database_id or user_id") from e

        Database = request.env["glodo.instance.database"]
        RemoteUser = request.env["glodo.remote.user"]

        database = Database.browse(database_id)
        if not database.exists():
            raise NotFound("Database not found")

        remote_user = RemoteUser.browse(user_id)
        if not remote_user.exists():
            raise NotFound("Remote user not found")

        if remote_user.database_id.id != database.id:
            raise BadRequest("User does not belong to this database")

        instance = database.instance_id
        if not instance.active:
            raise Forbidden("Instance is not active")

        if remote_user.is_archived:
            raise Forbidden("Cannot become an archived user")

        # Create encrypted payload
        crypto = instance._get_crypto()
        payload = {
            "database": database.name,
            "user_id": remote_user.remote_id,
        }
        encrypted_data = crypto.encrypt(payload)

        become_url = f"{instance.url.rstrip('/')}/glodo_cloud/become"

        # Build auto-submit form
        iv_val = encrypted_data["iv"]
        ct_val = encrypted_data["ciphertext"]
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Redirecting to {instance.name}...</title>
        </head>
        <body>
            <p>Redirecting to {instance.name} as {remote_user.login}...</p>
            <form id="become_form" method="POST" action="{become_url}">
                <input type="hidden" name="iv" value="{iv_val}" />
                <input type="hidden" name="ciphertext" value="{ct_val}" />
                <noscript>
                    <button type="submit">Click here to continue</button>
                </noscript>
            </form>
            <script>
                document.getElementById('become_form').submit();
            </script>
        </body>
        </html>
        """

        return request.make_response(
            html,
            headers=[("Content-Type", "text/html")],
        )
