from odoo.tests.common import TransactionCase

from odoo.addons.queue_job.exception import RetryableJobError

from ..components.abstract import AbstractEdiComponent
from ..exceptions import EdiException


class DotDict(dict):
    """Dotted notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class TestSafeEvalUnwrapsException(TransactionCase):
    def setUp(self):
        super().setUp()

        # This is a fake work_context, and not how we'd normally want to test
        # this, but theres no point in generating a whole bunch of stuff just to
        # call what is effectively almost a static method.
        # If we test more than the _safe_eval method this should be modified to
        # use the connector testing suite of tools.
        self.work_context = DotDict(
            {
                "model": self.env["res.partner"],
                "env": DotDict(
                    {
                        "user": {},
                    }
                ),
                "backend_record": None,
            }
        )

    def test_ensure_edi_exception_unwraps(self):
        abstract = AbstractEdiComponent(self.work_context)

        with self.assertRaises(EdiException):
            abstract._safe_eval('raise EdiException("Test")')

    def test_ensure_queue_job_retryablejoberror_exception_unwraps(self):
        abstract = AbstractEdiComponent(self.work_context)

        with self.assertRaises(RetryableJobError):
            abstract._safe_eval('raise RetryableJobError("Test")')

    def test_ensure_keyerror_wrapped(self):
        abstract = AbstractEdiComponent(self.work_context)

        with self.assertRaises(ValueError):
            abstract._safe_eval("[][1]")
