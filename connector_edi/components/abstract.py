import base64
import csv
import io
import re
from ast import literal_eval

import lxml
import lxml.builder as builder
import lxml.etree
import lxml.objectify
import requests

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import escape_psql, mimetypes
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

        try:
            wrapped_wdb = wrap_module(__import__("wdb"), ["set_trace"])
        except ImportError:
            wrapped_wdb = None

        return {
            # Odoo env
            "env": self.env,
            "model": self.model.sudo(),
            "user": self.env.user,
            "_": _,
            "backend": getattr(self, "backend_record", None),
            # Date & Time related
            "time": time,
            "datetime": datetime,
            "dateutil": dateutil,
            "pytz": pytz,
            # Misc. formatting, etc.
            "re": wrap_module(
                re,
                [
                    "split",
                    "match",
                    "search",
                    "sub",
                ],
            ),
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
            "getattr": getattr,
            "hasattr": hasattr,
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
            "mimetypes": wrap_module(
                mimetypes,
                [
                    "guess_mimetype",
                ],
            ),
            "type": type,
            "escape_psql": escape_psql,
            # Exceptions
            "EdiUnknownMessageType": EdiUnknownMessageType,
            "EdiException": EdiException,
            "UserError": UserError,
            "ValidationError": ValidationError,
            "OSError": OSError,
            "RetryableJobError": RetryableJobError,
            # Debuggers
            "wdb": wrapped_wdb,
        }

    def _safe_eval(self, code, **kwargs):
        eval_context = self._get_default_eval_context()
        eval_context.update(kwargs)

        # if backend_record is present, pull any configuration from that
        if hasattr(self, "backend_record"):
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

        try:
            safe_eval(
                code, eval_context, mode="exec", nocopy=True
            )  # nocopy allows to return 'action'

            return eval_context.get("action")
        except ValueError as e:
            # safe_eval wraps most exceptions with ValueError.
            # We want to behave slightly differently in some circumstances,
            # so we'll look at the inner exception and re-throw that
            # thus allowing the job queue to requeue jobs
            if isinstance(e.__context__, (EdiException, RetryableJobError)):
                # we want to erase the ValueError in this particular
                # circumstance, so not using raise from syntax is OK
                raise e.__context__  # noqa: disable=B904
            raise e


class AbstractEdiBinding(models.AbstractModel):
    _name = "edi.binding"
    _inherit = "external.binding"
    _description = "EDI Abstract Binding"

    backend_id = fields.Many2one(
        comodel_name="edi.backend",
        string="EDI Backend",
        required=True,
        ondelete="restrict",
    )
