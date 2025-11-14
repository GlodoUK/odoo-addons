import json
import logging

from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


# ruff: noqa: E501
def migrate(cr, version):
    _logger.info("credit_control/18.0.1.0.0/pre-upgrade.py running")

    if not column_exists(cr, "res_partner", "credit_control_limit"):
        _logger.warning(
            "credit_control/18.0.1.0.0/pre-upgrade.py skipped. The credit_control_limit column does not exist!"
        )
        return

    if not column_exists(cr, "res_partner", "credit_limit"):
        _logger.warning(
            "credit_control/18.0.1.0.0/pre-upgrade.py skipped. The credit_limit column does not exist!"
        )
        return

    cr.execute(
        """
        SELECT
            id
        FROM
            res_company
        """
    )

    company_ids = [row[0] for row in cr.fetchall()]

    cr.execute(
        """
        SELECT
            id, company_id, credit_control_limit
        FROM
            res_partner
        WHERE
            credit_control_limit > 0
        AND
            parent_id IS NULL
        """
    )

    for partner_id, company_id, credit_control_limit in cr.fetchall():
        if not company_id:
            credit_limit_data = {str(cid): credit_control_limit for cid in company_ids}
        else:
            credit_limit_data = {str(company_id): credit_control_limit}

        cr.execute(
            """
            UPDATE
                res_partner
            SET
                credit_limit = %s::jsonb
            WHERE
                id = %s
            """,
            [
                json.dumps(credit_limit_data),
                partner_id,
            ],
        )
