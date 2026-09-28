import logging

from odoo import api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Context flag guarding against the create/write hooks re-entering sync (the
# sync itself writes the backing-record field back onto the record). Mirrors
# the `..._skip_cron_sync` flag the old connector_edi route used.
_SKIP = "autopilot_skip_sync"


class AutopilotMixin(models.AbstractModel):
    """Mixin that self-manages the ``ir.cron`` / ``base.automation`` declared on
    a model's methods with ``@cron`` / ``@automation``.

    This is the trigger engine. Surfacing a backend in the Autopilot app is
    separate - a connector parents its own menu under the app (see the README) -
    and independent of this mixin. Inherit this whenever a model wants a
    self-managed schedule or event handler::

        class Thing(models.Model):
            _inherit = ["autopilot.mixin"]

            cleanup_cron_id = fields.Many2one("ir.cron", copy=False)

            @cron("cleanup_cron_id", interval_number=1, interval_type="days")
            def _cleanup(self): ...

    On create/write it materialises and keeps in step the backing records
    (schedule/active read from the fields the decorator names), storing each in
    the ``Many2one`` the decorator points at, and tears them down on unlink. It
    stores *no* fields of its own - purely behaviour.
    """

    _name = "autopilot.mixin"
    _description = "Autopilot Mixin"

    # ------------------------------------------------------------------
    # Spec discovery (decorated methods) + per-record value resolution
    # ------------------------------------------------------------------
    def _autopilot_specs(self):
        """Every decorated trigger on this model, as dicts
        ``{method, kind, spec}`` - one per decorator."""
        specs = []
        cls = type(self)
        for attr_name in dir(cls):
            try:
                attr = getattr(cls, attr_name)
            except Exception:  # noqa: BLE001 - defensive over odd descriptors
                continue
            for spec in getattr(attr, "_autopilot_crons", ()):
                specs.append({"method": attr_name, "kind": "cron", "spec": spec})
            for spec in getattr(attr, "_autopilot_automations", ()):
                specs.append({"method": attr_name, "kind": "automation", "spec": spec})
        return specs

    def _autopilot_resolve(self, value):
        """Resolve a decorator argument against a single record: a callable is
        called with the record, a field name is read from it, anything else is
        used literally."""
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
        """The Many2one on this model that stores the spec's backing record,
        validated to exist."""
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
        """Fields whose change should trigger a re-sync: everything a spec
        reads, plus the usual name/active."""
        watched = {"active", "name"}
        for entry in self._autopilot_specs():
            for key in ("interval_number", "interval_type", "active"):
                value = entry["spec"].get(key)
                if isinstance(value, str) and value in self._fields:
                    watched.add(value)
        return watched

    def _autopilot_dynamic(self):
        """True if any spec carries a callable argument. A lambda is opaque -
        we cannot introspect which fields it reads - so once one is present any
        write re-syncs (rather than silently going stale). A model that wants a
        lambda to react to a specific field only can still name that field in
        another arg, or keep the value a plain field reference."""
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
        """Persist a freshly-created backing record onto its Many2one without
        re-triggering sync."""
        self.with_context(**{_SKIP: True}).write({field: record.id})

    # ------------------------------------------------------------------
    # Backing-record builders
    # ------------------------------------------------------------------
    def _autopilot_trigger_name(self, spec, method):
        return spec.get("name") or f"{self.display_name}: {method}"

    def _autopilot_code(self, method, delay, with_records):
        """The Python the backing ``ir.cron`` / ``base.automation`` runs: a
        direct call to the decorated method on this record. ``delay`` (truthy)
        routes it through ``queue_job.with_delay``, forwarding a dict of
        options; ``with_records`` passes the automation's triggered recordset."""
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
        # A resolved domain may come back as a Python list (e.g. from a lambda
        # scoping to this record) or already as a string; filter_domain is a
        # Char, so normalise a list to its string form.
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
