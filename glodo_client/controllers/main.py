"""
Glodo Cloud Client Controllers.

These endpoints are called by the Glodo Cloud server to manage this
Odoo instance. Most endpoints require AES-GCM authentication using
the shared secret established during enrollment.
"""

import json
import logging
import time

from werkzeug.exceptions import BadRequest, Forbidden, NotFound
from werkzeug.utils import redirect

import odoo
from odoo import SUPERUSER_ID, api
from odoo.http import Controller, request, route
from odoo.modules.registry import Registry
from odoo.service.db import list_dbs
from odoo.tools import cloc

from ..utils.crypto import (
    get_client_config,
    glodo_authenticated,
)

_logger = logging.getLogger(__name__)


def get_db_registry(db_name: str) -> Registry:
    """Get registry for a database, with validation."""
    try:
        return Registry(db_name)
    except Exception as e:
        raise NotFound(f"Database '{db_name}' not accessible: {e}") from e


class GlodoCloudClient(Controller):
    """
    Controller endpoints for Glodo Cloud client functionality.

    Endpoints are server-wide (not database-specific) and use
    AES-GCM encryption for authentication.
    """

    @route(
        "/glodo_cloud/ping",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    def ping(self, **kwargs):
        """Simple health check endpoint (unauthenticated)."""
        instance_id, _ = get_client_config()
        return request.make_response(
            json.dumps(
                {
                    "status": "ok",
                    "timestamp": int(time.time()),
                    "enrolled": instance_id is not None,
                }
            ),
            headers=[("Content-Type", "application/json")],
        )

    @route(
        "/glodo_cloud/info",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    @glodo_authenticated
    def info(self, **kwargs):
        """
        Return instance information including all compatible databases.

        Response includes:
        - Instance-level information (Odoo version, etc.)
        - List of databases with CLOC and module info
        """
        # payload available via request.glodo_payload if needed

        # Instance-level info
        result = {
            "instance": {
                "odoo_version": odoo.release.version,
                "server_version_info": list(odoo.release.version_info),
            },
            "databases": [],
        }

        # Discover databases
        try:
            all_dbs = list_dbs(force=True)
        except Exception as e:
            _logger.warning("Could not list databases: %s", e)
            all_dbs = []

        # Gather info for each compatible database
        for db_name in all_dbs:
            db_info = self._get_database_info(db_name)
            if db_info:
                result["databases"].append(db_info)

        return request.make_response(
            json.dumps(result),
            headers=[("Content-Type", "application/json")],
        )

    def _get_database_info(self, db_name: str) -> dict:
        """Gather information about a specific database."""
        try:
            registry = Registry(db_name)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})

                # Count users
                user_count = env["res.users"].search_count(
                    [
                        ("share", "=", False),
                        ("active", "=", True),
                    ]
                )

                # Get installed modules
                modules = env["ir.module.module"].search([("state", "=", "installed")])
                module_list = [
                    {
                        "name": m.name,
                        "version": m.installed_version or "",
                    }
                    for m in modules
                ]

                db_info = {
                    "name": db_name,
                    "user_count": user_count,
                    "installed_modules": module_list,
                    "cloc": {},
                }

                # Try to get CLOC
                try:
                    cl = cloc.Cloc()
                    cl.count_customization(env)

                    db_info["cloc"] = {
                        "output": cl.report(),
                        "returncode": cl.code,
                    }
                except Exception as e:
                    db_info["cloc"] = {"error": str(e)}

                return db_info

        except Exception as e:
            _logger.warning("Could not get info for database %s: %s", db_name, e)
            return None

    @route(
        "/glodo_cloud/users",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    @glodo_authenticated
    def users(self, **kwargs):
        """
        Return users for a specific database.

        Payload: {"database": "db_name"}
        """
        payload = getattr(request, "glodo_payload", {})
        db_name = payload.get("database")

        if not db_name:
            raise BadRequest("Missing 'database' in request payload")

        try:
            registry = Registry(db_name)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})

                users = (
                    env["res.users"]
                    .with_context(active_test=False)
                    .search([("share", "=", False)])
                )

                user_list = [
                    {
                        "id": user.id,
                        "login": user.login,
                        "name": user.name,
                        "email": user.email or None,
                        "active": user.active,
                        "share": user.share,
                        "last_login": user.login_date.isoformat(
                            sep=" ", timespec="seconds"
                        )
                        if user.login_date
                        else None,
                    }
                    for user in users
                ]

            return request.make_response(
                json.dumps({"database": db_name, "users": user_list}),
                headers=[("Content-Type", "application/json")],
            )

        except Exception as e:
            _logger.error("Failed to get users for %s: %s", db_name, e)
            raise BadRequest(f"Failed to get users: {e}") from e

    @route(
        "/glodo_cloud/become",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    @glodo_authenticated
    def become(self, **kwargs):
        """
        Become a user on a specific database.

        Payload: {"database": "db_name", "user_id": 5}

        Creates a session for the specified user and redirects to /web.
        """
        payload = getattr(request, "glodo_payload", {})
        db_name = payload.get("database")
        user_id = payload.get("user_id")

        if not db_name:
            raise BadRequest("Missing 'database' in request payload")
        if not user_id:
            raise BadRequest("Missing 'user_id' in request payload")

        try:
            user_id = int(user_id)
        except (TypeError, ValueError) as e:
            raise BadRequest("Invalid user_id format") from e

        # Validate user exists and is suitable
        try:
            registry = Registry(db_name)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                user = env["res.users"].browse(user_id)

                if not user.exists():
                    raise NotFound(f"User {user_id} not found")
                if not user.active:
                    raise Forbidden("Cannot become an inactive user")
                if user.share:
                    raise Forbidden("Cannot become a portal/public user")

                login = user.login

        except (NotFound, Forbidden):
            raise
        except Exception as e:
            _logger.error("Failed to validate user %s in %s: %s", user_id, db_name, e)
            raise BadRequest(f"Failed to validate user: {e}") from e

        # Create session for the user
        request.session.db = db_name
        request.session.uid = user_id
        request.session.login = login

        # Compute session token
        try:
            registry = Registry(db_name)
            with registry.cursor() as cr:
                env = api.Environment(cr, user_id, {})
                user = env["res.users"].browse(user_id)
                request.session.session_token = user._compute_session_token(
                    request.session.sid
                )
        except Exception as e:
            _logger.warning("Could not compute session token: %s", e)

        _logger.info(
            "Glodo Cloud: Become user %s (ID: %d) in database %s",
            login,
            user_id,
            db_name,
        )

        return redirect("/web")

    @route(
        "/glodo_cloud/user_manage",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    @glodo_authenticated
    def user_manage(self, **kwargs):
        """
        Archive or unarchive a user on a specific database.

        Payload: {"database": "db_name", "user_id": 5, "action": "archive|unarchive"}
        """
        payload = getattr(request, "glodo_payload", {})
        db_name = payload.get("database")
        user_id = payload.get("user_id")
        action = payload.get("action")

        if not db_name:
            raise BadRequest("Missing 'database' in request payload")
        if not user_id:
            raise BadRequest("Missing 'user_id' in request payload")
        if action not in ("archive", "unarchive"):
            raise BadRequest("Invalid action. Must be 'archive' or 'unarchive'")

        try:
            user_id = int(user_id)
        except (TypeError, ValueError) as e:
            raise BadRequest("Invalid user_id format") from e

        try:
            registry = Registry(db_name)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})

                user = env["res.users"].with_context(active_test=False).browse(user_id)

                if not user.exists():
                    raise NotFound(f"User {user_id} not found")

                # Don't allow archiving admin
                if user_id in (1, 2):
                    raise Forbidden("Cannot modify system/admin users")

                new_active = action == "unarchive"
                user.write({"active": new_active})
                # We need explicit commit because we're using a raw cursor
                # from a different database context than the HTTP request
                env.cr.commit()  # pylint: disable=invalid-commit

                _logger.info(
                    "Glodo Cloud: User %s (ID: %d) %s in database %s",
                    user.login,
                    user_id,
                    "unarchived" if new_active else "archived",
                    db_name,
                )

            return request.make_response(
                json.dumps(
                    {
                        "success": True,
                        "database": db_name,
                        "user_id": user_id,
                        "active": new_active,
                    }
                ),
                headers=[("Content-Type", "application/json")],
            )

        except (NotFound, Forbidden):
            raise
        except Exception as e:
            _logger.error("Failed to %s user %s in %s: %s", action, user_id, db_name, e)
            raise BadRequest(f"Failed to {action} user: {e}") from e
