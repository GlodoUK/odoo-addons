import argparse

import odoo
import odoo.cli.neutralize
from odoo.cli.command import Command

# Absolute imports are required: this file is loaded as ``odoo.cli.shoehorn``
# (see odoo/cli/command.py load_addons_commands), so relative imports would
# resolve against ``odoo.cli``, not this addon.
# pylint: disable=odoo-addons-relative-import
from odoo.addons.shoehorn.generate import generate
from odoo.addons.shoehorn.migration import migrate


class Shoehorn(Command):
    """Repeatedly and safely bootstrap Odoo databases"""

    def run(self, cmdargs):
        parser = argparse.ArgumentParser(
            prog="odoo shoehorn",
            description="Repeatedly and safely bootstrap Odoo databases."
            " Inspired by Rails migrations and camptocamp/marabunta.",
        )
        subparsers = parser.add_subparsers(dest="command", required=True)

        common = argparse.ArgumentParser(add_help=False)
        common.add_argument(
            "--shoehorn-path",
            required=True,
            metavar="DIR",
            help="Directory of shoehorn files (YYYYMMDDHHMMSS_name.{py,xml,csv,sql})."
            " The directory's basename is the migration namespace.",
        )

        generate_parser = subparsers.add_parser(
            "generate",
            parents=[common],
            help="Create a new migration file and exit.",
        )
        generate_parser.add_argument(
            "name",
            metavar="NAME",
            help="Migration name, optionally with a .py/.xml/.csv/.sql"
            " extension (defaults to .py).",
        )

        apply_parser = subparsers.add_parser(
            "apply",
            parents=[common],
            help="Apply pending shoehorns to the database.",
            epilog="Unrecognised arguments are passed through to Odoo's config"
            " parser (e.g. -c /etc/odoo/odoo.conf, -d mydb).",
        )
        apply_parser.add_argument(
            "--shoehorn-namespace",
            metavar="NAME",
            help="Override the migration namespace (defaults to the basename"
            " of --shoehorn-path). Pinning it makes the applied log immune"
            " to directory renames.",
        )
        apply_parser.add_argument(
            "--neutralize",
            action="store_true",
            help="neutralize the database as the final step",
        )

        args, odoo_args = parser.parse_known_args(cmdargs)

        if args.command == "generate":
            # CLI output, not debugging
            print(generate(args.shoehorn_path, args.name))  # pylint: disable=print-used
            return

        # pass anything else to odoo to parse
        odoo.tools.config.parse_config(odoo_args)

        if args.command == "apply":
            migrate(args.shoehorn_path, namespace_override=args.shoehorn_namespace)

            if args.neutralize:
                input("Press Enter to continue with odoo neutralize...")
                odoo.cli.neutralize.Neutralize().run([])
