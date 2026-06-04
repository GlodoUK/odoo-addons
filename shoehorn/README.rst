========
shoehorn
========

Repeatedly and safely bootstrap Odoo databases.

shoehorn applies a directory of one-shot setup steps ("migrations") to a
database, tracking what has already been applied in the database itself - so
the same command can be applied against a fresh database, a half-bootstrapped
one, or a finished one, and always converges. It takes its inspiration from
Rails migrations and `camptocamp/marabunta
<https://github.com/camptocamp/marabunta>`__.


Plain `click-odoo <https://github.com/acsone/click-odoo>`__ scripts are
problematic because of the requirement to commit between steps: module installs
reset the registry mid-run, and later steps depend on the committed results
of earlier ones - so every migration gets its own registry, environment and
transaction.

.. code-block:: sh

    odoo shoehorn apply --shoehorn-path ./bootstrap -c /etc/odoo/odoo.conf

The module only needs to be on the addons path - Odoo discovers the command
from ``cli/shoehorn.py`` by filesystem convention; installing the module into
a database is a harmless no-op. The engine versions with Odoo itself: this
branch targets Odoo 19.

Usage
=====

A migration directory contains files named

.. code-block:: text

    YYYYMMDDHHMMSS_name.{py,xml,csv,sql}

e.g. ``20260604100000_install_modules.py``. Ordering is the filename sort;
the timestamp is the migration's identity.

``apply`` applies whatever is **pending**, in filename order, each in its own
transaction with a fresh registry. Applied migrations are recorded (by
timestamp) as a JSON list under an ``ir.config_parameter``
(``shoehorn.applied.<namespace>``) in the target database, written in the
same transaction as the migration - the log entry exists if and only if the
migration committed. So:

- a fresh/dropped database starts from zero, automatically;
- re-running after a failure picks up exactly where it stopped;
- there is no resume, rerun or rollback - never edit an applied migration,
  write a new one.

The module list is refreshed (``ir.module.module.update_list``) on every
invocation, before pending shoehorns are applied.

Concurrent runs are guarded by a session-level Postgres advisory lock held
for the duration of the run - a second ``apply`` against the same database
fails fast rather than queueing (mirroring Rails'
``ConcurrentMigrationError``). The lock is per database, not per namespace:
migrations from different directories touch the same modules and records.

Namespaces
==========

The directory's basename is the migration **namespace**, and each namespace
has its own applied log. So alongside a long-lived ``./bootstrap`` directory
you can keep separate directories for one-off complex fix-ups, each applied
and tracked independently:

.. code-block:: sh

    odoo shoehorn apply --shoehorn-path ./bootstrap -c /etc/odoo/odoo.conf
    odoo shoehorn apply --shoehorn-path ./fixup_t12345 -c /etc/odoo/odoo.conf

The namespace can be pinned explicitly with ``--shoehorn-namespace NAME``,
which takes precedence over the basename. Two consequences of "the basename
is the identity" when it is not pinned:

- **renaming a directory renames the namespace** - the new name starts from
  an empty log (everything is pending again) and a fresh ir.model.data
  module (re-applying creates duplicate records instead of updating);
- two different paths with the same basename share a log.

Namespaces must match ``[a-z0-9][a-z0-9_]*`` (no dots or dashes - the
namespace is embedded in xmlids, which split on the first dot).

Records created by data migrations are namespaced per migration namespace
(``__shoehorn_<namespace>__``), so directories can't silently clobber each
other's records by reusing an id. Referencing or updating another
namespace's records is still possible, just explicit:
``<record id="__shoehorn_bootstrap__.some_record">``.

Generating migrations
=====================

.. code-block:: sh

    odoo shoehorn generate add_a_thing --shoehorn-path ./bootstrap      # .py (default)
    odoo shoehorn generate res_partner.xml --shoehorn-path ./bootstrap  # data file
    odoo shoehorn generate ir.model.access.csv --shoehorn-path ./bootstrap  # data file

creates e.g. ``20260604164512_add_a_thing.py`` with the conventional stub.

Conventions
===========

- ``.py`` migrations must define ``up(env)``. Context is passed as keyword
  arguments to whichever of these parameters the function declares (or all
  of them via ``**kwargs``): ``namespace``, and ``module`` - the namespace's
  ir.model.data module, for xmlids consistent with data files, e.g.
  ``def up(env, module): env.ref(f"{module}.some_record")``.
- ``.xml``/``.csv``/``.sql`` are loaded via ``odoo.tools.convert``; records
  are namespaced under the ``__shoehorn_<namespace>__`` ir.model.data
  module. For ``.csv`` the name part of the filename must be the model name
  (``..._res.partner.csv``).
- Subdirectories and non-migration extensions are ignored - keep assets
  (logos etc.) and READMEs there.
- Files with migration extensions that don't match the naming convention are
  an error, not a warning.
- Prefer data files over Python: XML can update existing records
  (``<record id="base.main_company">``) and execute wizards
  (``<function model="res.config.settings" name="execute">``). Use ``.py``
  for what XML can't express - e.g. binary fields, which
  ``<field file="..."/>`` can't load outside a real addon directory.

Reusable helpers for ``.py`` migrations live in ``shoehorn/tools/``:

.. code-block:: python

    from odoo.addons.shoehorn.tools import (
        install_modules,           # install_modules(env, ["sale", "stock"])
        install_addons_yaml,       # doodba addons.yaml (explicitly named addons)
        install_private_modules,   # everything in src/private
    )

CLI
===

- ``odoo shoehorn generate NAME --shoehorn-path DIR`` - create a new
  migration (NAME may carry a ``.py``/``.xml``/``.csv``/``.sql`` extension;
  defaults to ``.py``).
- ``odoo shoehorn apply --shoehorn-path DIR`` - apply pending migrations.
  ``--shoehorn-namespace NAME`` overrides the namespace (default: DIR's
  basename). ``--neutralize`` runs ``odoo neutralize`` afterwards. Anything
  unrecognised is passed through to Odoo's config parser (``-c``, ``-d``,
  ...).
