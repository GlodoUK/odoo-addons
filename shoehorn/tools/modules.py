"""Module-installation helpers for .py migrations."""

import logging
import os

import yaml

_logger = logging.getLogger("shoehorn")


def install_modules(env, modules):
    """Install modules by technical name; raise if any are unavailable."""
    found = env["ir.module.module"].search([("name", "in", list(modules))])
    missing = sorted(set(modules) - set(found.mapped("name")))
    for module in missing:
        _logger.critical(f"  Could not find module {module}")
    needs_action = found.filtered(lambda m: m.state != "installed")
    if needs_action:
        needs_action.button_immediate_install()
    # Re-search: button_immediate_install resets the registry
    still_not = env["ir.module.module"].search(
        [("name", "in", list(modules)), ("state", "!=", "installed")]
    )
    for module in still_not:
        _logger.critical(f"  {module.name} not installed")
    if missing or still_not:
        raise RuntimeError(
            "Modules missing or not installed: "
            + ", ".join(missing + still_not.mapped("name"))
        )


def install_addons_yaml(env, path="/opt/odoo/custom/src/addons.yaml"):
    """Install every explicitly named addon from a doodba addons.yaml."""
    _logger.info(f"  Installing modules from {path}")
    with open(path) as f:
        addons_yaml = yaml.safe_load(f)
    for repo, repo_addons in addons_yaml.items():
        addons = [a for a in repo_addons if a != "*"]
        if not addons:
            continue
        _logger.info(f"  Working on {repo}")
        install_modules(env, addons)


def install_private_modules(env, path="/opt/odoo/custom/src/private"):
    """Install every module found in the private addons directory."""
    _logger.info(f"  Installing modules from {path}")
    private_addons = [
        f.name
        for f in os.scandir(path)
        if (
            f.is_dir()
            and not f.name.startswith(".")
            and os.path.exists(os.path.join(f.path, "__manifest__.py"))
        )
    ]
    install_modules(env, private_addons)
