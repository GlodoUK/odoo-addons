import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Starting helpdesk_privacy pre-fix_upgrade_views.py")

    env = api.Environment(cr, SUPERUSER_ID, {})

    view_id = env.ref(
        "helpdesk_privacy.helpdesk_privacy_tickets_followup",
        raise_if_not_found=False,
    )

    if view_id:
        view_id.unlink()

    _logger.info("Finishing helpdesk_privacy pre-fix_upgrade_views.py")
