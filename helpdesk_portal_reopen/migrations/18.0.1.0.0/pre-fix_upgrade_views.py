import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Starting helpdesk_portal_reopen pre-fix_upgrade_views.py")

    env = api.Environment(cr, SUPERUSER_ID, {})

    view_id = env.ref(
        "helpdesk_portal_reopen.helpdesk_portal_reopen_tickets_followup_reopen_ticket",
        raise_if_not_found=False,
    )

    if view_id:
        view_id.unlink()

    _logger.info("Finishing helpdesk_portal_reopen pre-fix_upgrade_views.py")
