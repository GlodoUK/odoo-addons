import base64
import collections
import csv
import datetime
import io
import json
import time
import re
from ast import literal_eval

import lxml
import pandas
import requests
from dateutil import relativedelta, rrule

import odoo
from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.component.core import AbstractComponent
from odoo.addons.queue_job.exception import RetryableJobError

from ..exceptions import EdiException, EdiUnknownMessageType


class AbstractEdiComponent(AbstractComponent):
    _name = "edi.connector"
    _inherit = "base.connector"
    _collection = "edi.backend"

    def _get_default_eval_context(self):
        """
        Prepare a default context to be used when evaluating python code, like the
        python formulas or code server actions.
        """

        try:
            import wdb
        except ImportError:
            wdb = None

        try:
            import debugpy
        except ImportError:
            debugpy = None

        return {
            # Odoo env
            "env": self.env,
            "model": self.model.sudo(),
            "user": self.env.user,
            "odoo": odoo,
            "_": _,
            "backend": self.backend_record,
            # Date & Time related
            "time": time,
            "datetime": datetime,
            "relativedelta": relativedelta,
            "rrule": rrule,
            # Misc. formatting, etc.
            "base64": base64,
            "csv": csv,
            "next": next,
            "iter": iter,
            "getattr": getattr,
            "hasattr": hasattr,
            "pd": pandas,
            "io": io,
            "json": json,
            "requests": requests,
            "literal_eval": literal_eval,
            "OrderedDict": collections.OrderedDict,
            "lxml": lxml,
            "re": re,
            # Exceptions
            "EdiUnknownMessageType": EdiUnknownMessageType,
            "EdiException": EdiException,
            "UserError": UserError,
            "ValidationError": ValidationError,
            "OSError": OSError,
            "RetryableJobError": RetryableJobError,
            # Debugging tools that should not be used in production
            "wdb": wdb,
            "debugpy": debugpy,
        }

    def _safe_eval(self, code, **kwargs):
        eval_context = self._get_default_eval_context()
        eval_context.update(kwargs)

        # Automatically inject any secrets as SECRET_KEY_NAME
        eval_context.update(
            {
                ("SECRET_{}".format(secret_id.key)): secret_id.value
                for secret_id in self.backend_record.secret_ids
            }
        )

        # Automatically inject any
        if self.backend_record.common_code:
            safe_eval(
                self.backend_record.common_code.strip(),
                eval_context,
                mode="exec",
                nocopy=True,
            )

            # Remove anything prefixed with _
            delete = [k for k in eval_context if k.startswith("_") and k != "_"]
            for k in delete:
                del eval_context[k]

        safe_eval(
            code, eval_context, mode="exec", nocopy=True
        )  # nocopy allows to return 'action'

        return eval_context.get("action")


class AbstractEdiBinding(models.AbstractModel):
    _name = "edi.binding"
    _inherit = "external.binding"

    backend_id = fields.Many2one(
        comodel_name="edi.backend",
        string="EDI Backend",
        required=True,
        ondelete="restrict",
    )
