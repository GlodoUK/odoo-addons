import logging

from odoo import api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Sync writes the backing record's Many2one back onto the record; this stops
# that write syncing again.
_SKIP = "autopilot_skip_sync"


class AutopilotMixin(models.AbstractModel):
    """Keeps the ``ir.cron`` and ``base.automation`` records behind a model's
    ``@cron`` / ``@automation`` methods in step with each record: created and
    updated on create/write, removed on unlink. Adds no fields. See the README.
    """

    _name = "autopilot.mixin"
    _description = "Autopilot Mixin"

    # ------------------------------------------------------------------
    # Spec discovery (decorated methods) + per-record value resolution
    # ------------------------------------------------------------------
    def _autopilot_specs(self):
        """``{method, kind, spec}`` for every decorator on this model."""
        specs = []
        cls = type(self)
        for attr_name in dir(cls):
            try:
                attr = getattr(cls, attr_name)
            except Exception:  # noqa: BLE001  odd descriptors
                continue
            for spec in getattr(attr, "_autopilot_crons", ()):
                specs.append({"method": attr_name, "kind": "cron", "spec": spec})
            for spec in getattr(attr, "_autopilot_automations", ()):
                specs.append({"method": attr_name, "kind": "automation", "spec": spec})
        return specs

    def _autopilot_resolve(self, value):
        self.ensure_one()
        if callable(value):
            return value(self)
        if isinstance(value, str) and value in self._fields:
            return self[value]
        return value

    def _autopilot_active(self):
        self.ensure_one()
        return bool(self.active) if "active" in self._fields else True

    def _autopilot_field(self, spec):
        field = spec["field"]
        if field not in self._fields:
            raise ValidationError(
                self.env._(
                    "autopilot: %(model)s has no field %(field)r to store the "
                    "backing record in.",
                    model=self._name,
                    field=field,
                )
            )
        return field

    def _autopilot_watched_fields(self):
        watched = {"active", "name"}
        for entry in self._autopilot_specs():
            for key in ("interval_number", "interval_type", "active"):
                value = entry["spec"].get(key)
                if isinstance(value, str) and value in self._fields:
                    watched.add(value)
        return watched

    def _autopilot_dynamic(self):
        """Any callable argument? We can't see which fields a lambda reads, so
        then every write re-syncs rather than going stale."""
        for entry in self._autopilot_specs():
            if any(callable(value) for value in entry["spec"].values()):
                return True
        return False

    # ------------------------------------------------------------------
    # ORM hooks: keep the backing records in step with the record
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get(_SKIP):
            records.with_context(**{_SKIP: True})._autopilot_sync()
        return records

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get(_SKIP) and (
            self._autopilot_dynamic() or self._autopilot_watched_fields() & set(vals)
        ):
            self.with_context(**{_SKIP: True})._autopilot_sync()
        return res

    def unlink(self):
        self._autopilot_teardown()
        return super().unlink()

    # ------------------------------------------------------------------
    # Sync + teardown
    # ------------------------------------------------------------------
    def _autopilot_sync(self):
        for record in self:
            record._autopilot_sync_one()

    def _autopilot_sync_one(self):
        self.ensure_one()
        for entry in self._autopilot_specs():
            if entry["kind"] == "cron":
                self._autopilot_sync_cron(entry)
            else:
                self._autopilot_sync_automation(entry)

    def _autopilot_teardown(self):
        for record in self:
            for entry in record._autopilot_specs():
                backing = record[entry["spec"]["field"]]
                if backing:
                    backing.sudo().unlink()

    def _autopilot_store(self, field, record):
        self.with_context(**{_SKIP: True}).write({field: record.id})

    # ------------------------------------------------------------------
    # Backing-record builders
    # ------------------------------------------------------------------
    def _autopilot_trigger_name(self, spec, method):
        return spec.get("name") or f"{self.display_name}: {method}"

    def _autopilot_code(self, method, delay, with_records):
        target = f"env[{self._name}].browse({self.id})"
        if delay:
            options = delay if isinstance(delay, dict) else {}
            kwargs = ", ".join(f"{k}={v!r}" for k, v in options.items())
            target += f".with_delay({kwargs})"
        records = "record" if with_records else ""
        return f"{target}.{method}({records})"

    def _autopilot_sync_cron(self, entry):
        self.ensure_one()
        spec = entry["spec"]
        field = self._autopilot_field(spec)
        vals = {
            "name": self._autopilot_trigger_name(spec, entry["method"]),
            "model_id": self.env["ir.model"]._get_id(self._name),
            "state": "code",
            "code": self._autopilot_code(
                entry["method"], spec.get("delay"), with_records=False
            ),
            "interval_number": int(self._autopilot_resolve(spec["interval_number"])),
            "interval_type": self._autopilot_resolve(spec["interval_type"]),
            "active": bool(self._autopilot_resolve(spec["active"])),
            "user_id": self.env.uid,
        }
        existing = self[field]
        if existing:
            existing.sudo().write(vals)
        else:
            cron = self.env["ir.cron"].sudo().create(vals)
            self._autopilot_store(field, cron)

    def _autopilot_sync_automation(self, entry):
        self.ensure_one()
        spec = entry["spec"]
        field = self._autopilot_field(spec)
        model_id = self.env["ir.model"]._get_id(spec["model"])
        name = self._autopilot_trigger_name(spec, entry["method"])
        # filter_domain is a Char; a lambda may return a list.
        domain = self._autopilot_resolve(spec["domain"])
        if not isinstance(domain, str):
            domain = str(domain)
        code = self._autopilot_code(
            entry["method"], spec.get("delay"), with_records=True
        )
        auto_vals = {
            "name": name,
            "model_id": model_id,
            "trigger": spec["trigger"],
            "filter_domain": domain or "[]",
            "active": bool(self._autopilot_resolve(spec["active"])),
        }
        existing = self[field]
        if existing:
            existing.sudo().write(auto_vals)
            server = existing.action_server_ids[:1]
            if server:
                server.sudo().write({"code": code, "model_id": model_id})
        else:
            automation = self.env["base.automation"].sudo().create(auto_vals)
            self.env["ir.actions.server"].sudo().create(
                {
                    "name": name,
                    "base_automation_id": automation.id,
                    "model_id": model_id,
                    "state": "code",
                    "code": code,
                    "usage": "base_automation",
                }
            )
            self._autopilot_store(field, automation)
