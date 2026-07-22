from datetime import datetime

import feedparser


def parse_feed(raw):
    """Parse RSS or Atom feed markup into item dictionaries."""
    parsed = feedparser.parse(raw)
    return [
        {
            "title": entry.get("title"),
            "link": entry.get("link"),
            "guid": entry.get("id") or entry.get("link"),
            "published": _parse_date(entry),
            "summary": _summary(entry),
            "category": _category(entry),
            "author": entry.get("author"),
        }
        for entry in parsed.entries
    ]


def _category(entry):
    """Join an entry's categories/tags (``<category>`` in both RSS and Atom)."""
    terms = [tag.get("term") for tag in entry.get("tags", []) if tag.get("term")]
    return ", ".join(terms) or None


def _summary(entry):
    """Prefer the richest markup an entry offers (Atom content over summary)."""
    content = entry.get("content")
    if content:
        return content[0].get("value")
    return entry.get("summary")


def _parse_date(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return False
    return datetime(*parsed[:6])
