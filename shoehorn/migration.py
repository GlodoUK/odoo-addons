"""Discovering and applying migrations - see README.rst for the model."""

import contextlib
import inspect
import json
import logging
import os
import re
import zlib

import psycopg2

import odoo
from odoo.tools.convert import (
    convert_csv_import,
    convert_sql_import,
    convert_xml_import,
)

try:
    # Doodba images ship click-odoo; prefer its environment handling (user
    # context, registry/connection teardown, cross-version compatibility).
    from click_odoo import OdooEnvironment
except ImportError:

    @contextlib.contextmanager
    def OdooEnvironment(database):
        """Minimal stand-in for click_odoo.OdooEnvironment."""
        registry = odoo.modules.registry.Registry(database)
        try:
            with registry.cursor() as cr:
                # cursor context manager commits on success, rolls back on error
                yield odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        finally:
            odoo.modules.registry.Registry.delete(database)
            odoo.sql_db.close_db(database)


_logger = logging.getLogger("shoehorn")

# ir.model.data namespace for records created by data migrations, per
# migration namespace: __shoehorn_<namespace>__. Unshared so directories
# can't silently clobber each other's records by reusing an id;
# cross-namespace references must be fully qualified.
MODULE_FORMAT = "__shoehorn_{}__"
# Applied log parameter, per namespace: shoehorn.applied.<namespace>
STATE_PARAM_PREFIX = "shoehorn.applied"
# Constant, deterministic key for the per-database advisory lock
ADVISORY_LOCK_KEY = zlib.crc32(b"shoehorn")
EXTENSIONS = ("py", "xml", "csv", "sql")
TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"
FILENAME_RE = re.compile(
    r"^(?P<version>\d{14})"
    r"_(?P<name>[a-z0-9][a-z0-9._]*)"
    r"\.(?P<ext>py|xml|csv|sql)$"
)
# No dots or dashes: the namespace is embedded in the ir.model.data module
# name, and xmlids split on the first dot.
NAMESPACE_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")


def namespace(directory, override=None):
    """
    The migration namespace: `override` if given, else `directory`'s
    basename. Each namespace has its own applied log, so e.g. ./bootstrap
    and a one-off ./fixup_t12345 are tracked independently. Renaming a
    directory renames the namespace - the new name starts from an empty
    log - unless the namespace is pinned with `override`.
    """
    name = override or os.path.basename(os.path.normpath(os.path.abspath(directory)))
    if not NAMESPACE_RE.match(name):
        raise ValueError(
            f"'{name}' is not a valid migration namespace;"
            " it must match [a-z0-9][a-z0-9_]*."
        )
    return name


def migrations(directory):
    """
    Sorted (version, name, ext, path) tuples for the migration files in
    `directory` (top level only). Files with migration extensions must match
    the naming convention; anything else is ignored.
    """
    directory = os.path.abspath(directory)
    found = []
    for entry in sorted(os.scandir(directory), key=lambda e: e.name):
        if not entry.is_file():
            continue
        ext = os.path.splitext(entry.name)[1].lower().lstrip(".")
        if ext not in EXTENSIONS:
            continue
        match = FILENAME_RE.match(entry.name)
        if not match:
            raise ValueError(
                f"'{entry.name}' does not match the migration naming convention"
                " YYYYMMDDHHMMSS_name.{py,xml,csv,sql}."
            )
        found.append((match["version"], match["name"], match["ext"], entry.path))

    versions = [version for version, _, _, _ in found]
    duplicates = {v for v in versions if versions.count(v) > 1}
    if duplicates:
        raise ValueError(
            "Duplicate migration timestamps: " + ", ".join(sorted(duplicates))
        )
    return found


def _apply_python(env, path, **context):
    with open(path, "rb") as f:
        code = f.read()
    scope = {"__name__": "shoehorn.migration", "__file__": path}
    exec(compile(code, path, "exec"), scope)
    up = scope.get("up")
    if not callable(up):
        raise ValueError(f"Migration '{os.path.basename(path)}' must define up(env).")
    # Context is passed as keyword arguments, filtered to what up() declares:
    # up(env), up(env, module=...), and up(env, **kwargs) all work.
    params = inspect.signature(up).parameters
    if not any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
        context = {k: v for k, v in context.items() if k in params}
    up(env, **context)


def _apply_data(env, module, path, name, ext):
    idref = {}
    if ext == "csv":
        # convert_csv_import derives the model from the file name, so pass
        # the name part without the timestamp prefix
        with open(path, "rb") as f:
            content = f.read()
        convert_csv_import(env, module, f"{name}.csv", content, idref, "init", True)
    elif ext == "sql":
        with open(path, "rb") as f:
            convert_sql_import(env, f)
    else:
        # convert_xml_import accepts a path; file objects must have a .name
        convert_xml_import(env, module, path, idref, "init", True)


def _db_name():
    db_name = odoo.tools.config.get("db_name")
    if isinstance(db_name, (list, tuple)):
        db_name = db_name[0]
    return db_name


@contextlib.contextmanager
def _advisory_lock(db_name):
    """
    Hold a session-level Postgres advisory lock for the duration of the run
    so concurrent invocations can't double-apply migrations; like Rails, a
    second runner fails fast rather than queueing.

    A dedicated psycopg2 connection is required: each migration's environment
    closes Odoo's connection pool on teardown, which would release a lock
    held on a pooled connection. Advisory lock keys are scoped per database,
    so different databases migrate concurrently without contention.
    """
    _, connection_info = odoo.sql_db.connection_info_for(db_name)
    connection = psycopg2.connect(**connection_info)
    try:
        # no transaction needed for a session-level lock, and autocommit
        # avoids sitting idle-in-transaction for the whole run
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute("SELECT pg_try_advisory_lock(%s)", (ADVISORY_LOCK_KEY,))
        if not cursor.fetchone()[0]:
            raise RuntimeError(
                f"Another shoehorn run is already migrating {db_name}"
                " (advisory lock held)."
            )
        yield
    finally:
        # disconnecting releases the session-level lock
        connection.close()


def migrate(directory, namespace_override=None):
    """Apply the directory's pending migrations to the database."""
    found = migrations(directory)
    ns = namespace(directory, namespace_override)
    state_param = f"{STATE_PARAM_PREFIX}.{ns}"
    module = MODULE_FORMAT.format(ns)
    db_name = _db_name()

    # One lock per database, not per namespace: migrations from different
    # directories touch the same modules and records.
    with _advisory_lock(db_name):
        # The applied log lives in the target database itself, so a fresh
        # database always starts from zero and re-running the command applies
        # only what is pending, regardless of which host runs it.
        with OdooEnvironment(database=db_name) as env:
            applied = json.loads(
                env["ir.config_parameter"].get_param(state_param) or "[]"
            )
        done = {entry["version"] for entry in applied}
        pending = [m for m in found if m[0] not in done]
        _logger.info(
            f"{len(found)} migrations in {os.path.abspath(directory)}"
            f" (namespace '{ns}');"
            f" {len(found) - len(pending)} applied, {len(pending)} pending."
        )

        # Built-in initial step: refresh the module list on every invocation
        with OdooEnvironment(database=db_name) as env:
            _logger.info("Updating module list.")
            env["ir.module.module"].update_list()

        for index, (version, name, ext, path) in enumerate(pending, start=1):
            filename = os.path.basename(path)
            _logger.info(f"[{index}/{len(pending)}] {filename}")
            try:
                # Each migration gets a fresh registry, env and transaction;
                # commit on success and rollback on error are handled by
                # OdooEnvironment.
                with OdooEnvironment(database=db_name) as env:
                    if ext == "py":
                        _apply_python(env, path, namespace=ns, module=module)
                    else:
                        _apply_data(env, module, path, name, ext)
                    # Record in the same transaction as the migration: the
                    # log entry exists if and only if the migration committed.
                    applied.append({"version": version, "name": name})
                    env["ir.config_parameter"].set_param(
                        state_param, json.dumps(applied)
                    )
            except Exception:
                _logger.critical(
                    f"Migration '{filename}' failed. Transaction rolled back."
                )
                raise

    _logger.info("Database is up to date.")
