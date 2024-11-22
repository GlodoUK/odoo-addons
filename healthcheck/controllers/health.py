import json

import werkzeug
from odoo import http, service
from odoo.addons.web.controllers.main import ensure_db
from odoo.tools import config


class Healthcheck(http.Controller):
    def _healthz_get_db_names(self):
        if config["db_name"]:
            db_names = config["db_name"].split(",")
        else:
            db_names = service.db.exp_list(True)
        return db_names

    @http.route("/healthz", type="http", auth="none", csrf=False)
    def status(self):
        ensure_db()

        # TODO: Can we figure out some way to check that there's a cron, job
        # queue, etc. is OK, and we can take into account start up time? Or is
        # this more a job for the prometheus module?
        headers = {"Content-Type": "application/json"}
        info = {"web": "OK", "db_names": self._healthz_get_db_names()}
        return werkzeug.wrappers.Response(json.dumps(info), headers=headers)
