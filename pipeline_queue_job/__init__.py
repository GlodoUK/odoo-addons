from . import models


def post_load():
    """Contribute the ``with_delay`` marking verb to pipeline core's Pipeline.

    Pipeline is a plain Python class (not an ORM model), so the engine attaches
    its marker here, once, when the module loads.
    """
    from odoo.addons.pipeline.pipeline import Pipeline

    from .pipeline import with_delay

    Pipeline.with_delay = with_delay
