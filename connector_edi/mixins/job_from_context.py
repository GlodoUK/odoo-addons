class MixinJobFromCtx:
    """
    Utility functions to fetch any job from the odoo env context
    """

    def _job_from_ctx(self):
        job = self.env["queue.job"].sudo()
        if self.env.context.get("job_uuid"):
            job = (
                self.env["queue.job"]
                .sudo()
                .search([("uuid", "=", self.env.context.get("job_uuid"))], limit=1)
            )
        return job
