"""
Glodo Cloud remote user model.

Represents a user on a remote Odoo database.
"""

import logging

from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class GlodoRemoteUser(models.Model):
    _name = "glodo.remote.user"
    _description = "Remote User on Managed Instance"
    _order = "database_id, name"

    name = fields.Char(
        required=True,
    )

    login = fields.Char(
        required=True,
    )

    email = fields.Char()

    remote_id = fields.Integer(
        string="Remote User ID",
        required=True,
        index=True,
    )

    database_id = fields.Many2one(
        "glodo.instance.database",
        string="Database",
        required=True,
        ondelete="cascade",
        index=True,
    )

    database_name = fields.Char(
        related="database_id.name",
        store=True,
    )

    instance_id = fields.Many2one(
        related="database_id.instance_id",
        store=True,
        index=True,
    )

    instance_name = fields.Char(
        related="database_id.instance_name",
        store=True,
    )

    instance_url = fields.Char(
        related="database_id.instance_url",
    )

    is_archived = fields.Boolean(
        default=False,
        help="Whether the user is archived/inactive on the remote instance",
    )

    last_login = fields.Datetime(
        readonly=True,
    )

    last_become_date = fields.Datetime(
        string="Last Become Action",
        readonly=True,
    )

    _sql_constraints = [
        (
            "unique_database_remote_id",
            "UNIQUE(database_id, remote_id)",
            "Remote user ID must be unique per database.",
        ),
    ]

    def action_become_user(self):
        """
        Initiate a 'become' action to log into the remote instance as this user.

        Creates a signed request and redirects the admin to the client's
        become endpoint.
        """
        self.ensure_one()

        if self.is_archived:
            raise UserError(self.env._("Cannot become an archived user."))

        database = self.database_id
        instance = database.instance_id

        if not instance.active:
            raise UserError(self.env._("Instance is not active."))

        self.env["glodo.action.log"].create(
            {
                "instance_id": instance.id,
                "remote_user_id": self.id,
                "admin_user_id": self.env.user.id,
                "action_type": "become",
                "payload": str(
                    {
                        "database": database.name,
                        "user_id": self.remote_id,
                        "admin_user": self.env.user.login,
                        "admin_user_id": self.env.user.id,
                    }
                ),
            }
        )

        self.last_become_date = fields.Datetime.now()

        _logger.info(
            "Glodo Cloud: Admin %s initiating become action for user %s on %s/%s",
            self.env.user.login,
            self.login,
            instance.name,
            database.name,
        )

        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/glodo_cloud/become_redirect?"
                f"database_id={database.id}&"
                f"user_id={self.id}"
            ),
            "target": "new",
        }

    def action_archive_user(self):
        """Archive this user on the remote instance."""
        self.ensure_one()

        if self.is_archived:
            raise UserError(self.env._("User is already archived."))

        database = self.database_id
        instance = database.instance_id

        try:
            instance._make_encrypted_request(
                "/glodo_cloud/user_manage",
                {
                    "database": database.name,
                    "user_id": self.remote_id,
                    "action": "archive",
                },
            )
        except Exception as e:
            _logger.error(
                "Failed to archive user %s on %s/%s: %s",
                self.login,
                instance.name,
                database.name,
                e,
            )
            raise

        self.env["glodo.action.log"].create(
            {
                "instance_id": instance.id,
                "remote_user_id": self.id,
                "admin_user_id": self.env.user.id,
                "action_type": "archive",
                "result": "success",
            }
        )

        self.is_archived = True

        _logger.info(
            "Glodo Cloud: User %s archived on %s/%s by admin %s",
            self.login,
            instance.name,
            database.name,
            self.env.user.login,
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("User Archived"),
                "message": self.env._(
                    "User %(user)s has been archived on %(db)s.",
                    user=self.login,
                    db=database.name,
                ),
                "type": "success",
                "sticky": False,
            },
        }

    def action_unarchive_user(self):
        """Unarchive this user on the remote instance."""
        self.ensure_one()

        if not self.is_archived:
            raise UserError(self.env._("User is not archived."))

        database = self.database_id
        instance = database.instance_id

        try:
            instance._make_encrypted_request(
                "/glodo_cloud/user_manage",
                {
                    "database": database.name,
                    "user_id": self.remote_id,
                    "action": "unarchive",
                },
            )
        except Exception as e:
            _logger.error(
                "Failed to unarchive user %s on %s/%s: %s",
                self.login,
                instance.name,
                database.name,
                e,
            )
            raise

        self.env["glodo.action.log"].create(
            {
                "instance_id": instance.id,
                "remote_user_id": self.id,
                "admin_user_id": self.env.user.id,
                "action_type": "unarchive",
                "result": "success",
            }
        )

        self.is_archived = False

        _logger.info(
            "Glodo Cloud: User %s unarchived on %s/%s by admin %s",
            self.login,
            instance.name,
            database.name,
            self.env.user.login,
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("User Unarchived"),
                "message": self.env._(
                    "User %(user)s has been unarchived on %(db)s.",
                    user=self.login,
                    db=database.name,
                ),
                "type": "success",
                "sticky": False,
            },
        }

    def action_toggle_archive(self):
        """Toggle the archive status of this user."""
        self.ensure_one()

        if self.is_archived:
            return self.action_unarchive_user()
        else:
            return self.action_archive_user()
