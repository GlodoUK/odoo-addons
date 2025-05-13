class MixinJobFromCtx:
    """
    Utility methods to fetch any job from the odoo env context
    """

    def _job_from_ctx(self):
        job_id = self.env["queue.job"].sudo()

        job_uuid = self.env.context.get("job_uuid")

        if job_uuid:
            job_id = (
                self.env["queue.job"].sudo().search([("uuid", "=", job_uuid)], limit=1)
            )

        return job_id
