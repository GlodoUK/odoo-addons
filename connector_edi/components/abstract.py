import base64
import csv
import io
from ast import literal_eval
from zipfile import ZipFile

import lxml
import lxml.builder as builder
import lxml.etree
import lxml.objectify
import requests

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import (
    datetime,
    dateutil,
    json,
    pytz,
    safe_eval,
    time,
    wrap_module,
)

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

        return {
            # Odoo env
            "env": self.env,
            "model": self.model.sudo(),
            "user": self.env.user,
            "_": _,
            "backend": self.backend_record,
            # Date & Time related
            "time": time,
            "datetime": datetime,
            "dateutil": dateutil,
            "pytz": pytz,
            # Misc. formatting, etc.
            "base64": wrap_module(
                base64,
                [
                    "b64encode",
                    "b64decode",
                ],
            ),
            "csv": wrap_module(
                csv,
                [
                    "writer",
                    "reader",
                    "DictReader",
                    "DictWriter",
                    "QUOTE_ALL",
                    "QUOTE_MINIMAL",
                    "QUOTE_NONNUMERIC",
                    "QUOTE_NONE",
                    "Error",
                ],
            ),
            "next": next,
            "iter": iter,
            "io": wrap_module(
                io,
                [
                    "StringIO",
                    "BytesIO",
                ],
            ),
            "json": json,
            "requests": wrap_module(
                requests,
                [
                    "get",
                    "post",
                    "head",
                    "patch",
                    "request",
                    "Session",
                ],
            ),
            "literal_eval": literal_eval,
            "lxml": wrap_module(
                lxml,
                {
                    "etree": lxml.etree.__all__,
                    "objectify": lxml.objectify.__all__,
                },
            ),
            "builder": wrap_module(
                builder,
                [
                    "E",
                ],
            ),
            # Exceptions
            "EdiUnknownMessageType": EdiUnknownMessageType,
            "EdiException": EdiException,
            "UserError": UserError,
            "ValidationError": ValidationError,
            "OSError": OSError,
            "RetryableJobError": RetryableJobError,
            "ZipFile": ZipFile,
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
