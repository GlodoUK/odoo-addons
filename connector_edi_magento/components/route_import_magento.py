import logging
import math
from datetime import datetime

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class EdiRouteMagentoOrderImporterComponent(Component):
    _name = "edi.route.importer.magento"
    _inherit = ["base.importer", "edi.connector"]
    _usage = "import.magento"
    _apply_on = "edi.envelope"

    # Fetch all the pages of a given endpoint
    # Available kwargs:
    #     start_date (optional): The start date to fetch from
    #       (False to fetch all since last update)
    #     end_date (optional): The end date to fetch to
    #       (False to fetch all until now)
    #     per_page (optional): The number of records to fetch per page
    #       (Default: 200)
    #     filters (optional): Dictionary of filters to apply
    #       Required by some endpoints
    #       See API Docs: https://developer.adobe.com/commerce/webapi/rest/quick-reference/
    #       https://developer.adobe.com/commerce/webapi/rest/use-rest/performing-searches/
    #       e.g.
    #       {
    #           "price": {
    #               "value": "100",
    #               "operation": "gt"
    #               # Leave blank for eq
    #           },
    #           "_or1": {
    #               "status": {
    #                   "value": "complete",
    #               },
    #               "status": {
    #                   "value": "closed",
    #               }
    #           }
    #       }
    #     single_page (optional): If True, only fetch one page
    #       (Default: False)
    #     current_page (optional): The current page number
    #       (Default: 1)
    #       Required if single_page is True
    #       Only used if single_page is True
    #     params (optional): The params to pass to the request
    #       (Default: None)
    #       Only used if single_page is True
    def run(self, route_id, **kwargs):
        if kwargs.get("single_page"):
            # Not the first run. Run one page only
            self._run_page(route_id, **kwargs)
            return

        # First run. Fetch info to queue pages

        # Fetch all the required args
        backend = self.backend_record
        endpoint = route_id.magento_endpoint
        if not endpoint:
            raise UserError(_("No endpoint specified"))

        if endpoint == "products/":
            # Fetch the attribute sets
            if route_id.magento_in_ignore_attributes:
                ignore_attributes = route_id.magento_in_ignore_attributes.split(",")
            else:
                ignore_attributes = []
            if route_id.magento_in_readonly_attributes:
                readonly_attributes = (
                    route_id.magento_in_readonly_attributes.split(",") or []
                )
            else:
                readonly_attributes = []
            self.env["magento.attribute"].fetch_magento_attributes(
                backend, ignore_attributes, readonly_attributes
            )

        endpoint_slug = endpoint.replace("/", "").upper()
        if endpoint_slug.startswith("_"):
            endpoint_slug = endpoint_slug[1:]
        if endpoint_slug.endswith("_"):
            endpoint_slug = endpoint_slug[:-1]

        start_date = kwargs.get("start_date", False)
        end_date = kwargs.get("end_date", False)

        last_update = backend.secret_ids.filtered(
            lambda s: s.key == "LASTFETCH%s" % endpoint_slug
        )
        if not last_update:
            last_update = self.env["edi.secret"].create(
                {
                    "backend_id": backend.id,
                    "key": "LASTFETCH%s" % endpoint_slug,
                    "value": "",
                }
            )

        if not start_date:
            start_date = last_update.value
        if not end_date:
            end_date = datetime.now().isoformat()

        filters = kwargs.get("filters", {})
        if not filters and route_id.magento_filters:
            filters = dict(route_id.magento_filters)

        # Set the "Last Update" date to the latest of the end date, last update date
        # This ensures that the next FULL run will only import new records
        end_date_datetime = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%f")
        if last_update.value:
            last_update_datetime = datetime.strptime(
                last_update.value, "%Y-%m-%dT%H:%M:%S.%f"
            )
            last_update.value = max(last_update_datetime, end_date_datetime).isoformat()
        else:
            last_update.value = end_date

        _logger.info(
            "Fetching page count from Magento %s for backend %s", endpoint, backend.name
        )

        # Establish Page Count
        current_page = 1
        per_page = kwargs.get("per_page", 200)
        params = self._create_params(start_date, end_date, per_page, **kwargs)
        response = backend.magento_send_request(endpoint, params=params)
        if response.status_code != 200:
            raise UserError(
                _(
                    "Error fetching {endpoint}} from Magento (Status: {status_code})"
                ).format(
                    endpoint=endpoint,
                    status_code=response.status_code,
                )
            )

        total_count = response.json()["total_count"]
        total_pages = math.ceil(total_count / per_page)

        if total_count == 0:
            return

        # Fetch all the pages
        while current_page <= total_pages:
            params["searchCriteria[currentPage]"] = current_page
            route_id.with_delay()._run_in(
                start_date=start_date,
                end_date=end_date,
                current_page=current_page,
                params=params,
                single_page=True,
                filters=filters,
            )
            current_page += 1

    def _run_page(self, route_id, **kwargs):
        backend = self.backend_record
        endpoint = route_id.magento_endpoint
        endpoint_slug = endpoint.replace("/", "").upper()
        if endpoint_slug.startswith("_"):
            endpoint_slug = endpoint_slug[1:]
        if endpoint_slug.endswith("_"):
            endpoint_slug = endpoint_slug[:-1]
        start_date = kwargs.get("start_date")
        end_date = kwargs.get("end_date")
        current_page = kwargs.get("current_page", 1)
        params = kwargs.get("params")

        _logger.info(
            "Fetching page %s from Magento %s for backend %s",
            current_page,
            endpoint,
            backend.name,
        )

        response = backend.magento_send_request(endpoint, params=params)
        if response.status_code != 200:
            raise UserError(
                _(
                    "Error fetching {endpoint}} from Magento (Status: {status_code})"
                ).format(
                    endpoint=endpoint,
                    status_code=response.status_code,
                )
            )
        self._make_envelope(
            response,
            route_id,
            endpoint_slug,
            start_date,
            end_date,
            current_page,
            params,
        )

    def _create_params(self, start_date, end_date, per_page, **kwargs):
        current_page = 1
        params = {
            "searchCriteria[currentPage]": current_page,
            "searchCriteria[pageSize]": per_page,
        }
        group_index = 0
        if start_date:
            params = self._make_filter_param(
                params,
                "updated_at",
                {"value": start_date, "operation": "gteq"},
                group_index,
            )
            group_index += 1
        if end_date:
            params = self._make_filter_param(
                params,
                "updated_at",
                {"value": end_date, "operation": "lt"},
                group_index,
            )
            group_index += 1
        if kwargs.get("filters"):
            for key, value in kwargs.get("filters").items():
                params = self._make_filter_param(params, key, value, group_index)
                group_index += 1
        return params

    def _make_filter_param(self, params, key, value, group_index, or_index=0):
        if key.startswith("_or"):
            for key2, value2 in value.items():
                params = self._make_filter_param(
                    params, key2, value2, group_index, or_index
                )
                or_index += 1
            return params
        params[
            "searchCriteria[filterGroups][%i][filters][%i][field]"
            % (group_index, or_index)
        ] = key
        params[
            "searchCriteria[filterGroups][%i][filters][%i][value]"
            % (group_index, or_index)
        ] = value.get("value")
        params[
            "searchCriteria[filterGroups][%i][filters][%i][conditionType]"
            % (group_index, or_index)
        ] = value.get("operation", "eq")
        return params

    def _make_envelope(
        self, response, route_id, endpoint_slug, start_date, end_date, page, params
    ):
        if not start_date:
            start_date = "NoStart"
        external_id = "MagentoIn-%s-%s-%s-%s" % (  # noqa: UP031
            endpoint_slug,
            start_date,
            end_date,
            page,
        )
        envelope_id = self.env["edi.envelope"].create(
            {
                "backend_id": self.backend_record.id,
                "direction": "in",
                "route_id": route_id.id,
                "body": response.text,
                "external_id": external_id,
                "content_filename": external_id + ".json",
            }
        )
        envelope_id.message_post(
            body=_("Request Parameters:\n{params}").format(
                params=params if params else "No Parameters Provided"
            )
        )
        envelope_id.action_pending()
