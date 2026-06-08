# The `odoo shoehorn` CLI command is discovered by filesystem convention
# (cli/shoehorn.py) and needs nothing from here. The models below are only
# used when the module is actually installed in a database, where they back
# the "Generate shoehorn migration" wizard; importing them is cheap (class
# definitions, no database access) and so harmless during CLI-only use.
from . import wizards
