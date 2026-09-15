import re

import idna

# RFC 1035, minus the trailing dot we strip during normalisation.
_DOMAIN_MAX_LENGTH = 253
# idna is happy with an all-numeric TLD, which no customer can send mail from,
# and which is what would let an IP address through.
_TLD_RE = re.compile(r"^[a-z]{2,63}$")


def normalize_domain(domain):
    """Return ``domain`` in the canonical form used for storage and matching.

    Lowercased, IDNA encoded, stripped of surrounding whitespace and of the
    optional trailing dot.

    Returns False for anything that is not a bare domain, so a falsy result
    doubles as the validation failure: an '@', a local part, a URL, a bare
    hostname with no dot and an IP address are all rejected.
    """
    if not domain or not isinstance(domain, str):
        return False

    try:
        # idna enforces the IDNA2008 + UTS-46 label rules for us: it rejects
        # '@', '_', spaces, hyphens at either end of a label and over-long
        # labels, lowercases, and encodes unicode to the punycode form that
        # incoming mail gives us.
        domain = idna.encode(domain.strip().rstrip("."), uts46=True).decode("ascii")
    except idna.IDNAError:
        return False

    labels = domain.split(".")
    if (
        len(domain) > _DOMAIN_MAX_LENGTH
        or len(labels) < 2
        or not _TLD_RE.match(labels[-1])
    ):
        return False

    return domain
