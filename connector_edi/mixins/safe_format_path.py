import datetime
import os
import re
import unicodedata


class MixinSafeFormatPath:
    """
    Utility functions to scan and move files
    """

    def _safe_format_path(self, path, **kwargs):
        opts = kwargs

        opts.update({"datetime": datetime.datetime.now()})

        # TODO assumes the path part is safe

        formatted_path = os.path.abspath(os.path.normpath(path.format(**opts)))

        formatted_file = os.path.splitext(os.path.basename(formatted_path))

        return os.path.join(
            os.path.dirname(formatted_path),
            "{file}{ext}".format(
                file=self._slugify(formatted_file[0]), ext=formatted_file[1]
            ),
        )

    def _slugify(self, s, lowercase=False):
        uni = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
        slug_str = re.sub(r"[^a-zA-Z0-9_\-\*]", " ", uni).strip()
        if lowercase:
            slug_str = slug_str.lower()
        return re.sub(r"[-\s]+", "-", slug_str)
