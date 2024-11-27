import io
import os
import typing
import warnings
from urllib.parse import urljoin, urlparse

import ftpparser
import pycurl


class Client:
    """
    An alternative to ftplib that uses pycurl, in order to avoid
    issues such as:
      * https://bugs.python.org/issue10808
      * https://bugs.python.org/issue19500
    """

    def __enter__(self):
        return self

    # Context management protocol: try to quit() if active
    def __exit__(self, *args):
        if self.client is not None:
            self.client.close()

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        connect_timeout: int = 5,
        max_retries: int = 5,
        use_ssl: typing.Union[None, bool] = None,
    ):
        parsed = urlparse(url)
        assert parsed.scheme in ("ftp", "ftps"), "Expected URL scheme is ftp or ftps"

        self.base_url = url
        self.username = username
        self.password = password
        self.connect_timeout = connect_timeout
        self.max_retries = max_retries
        if not use_ssl and parsed.scheme == "ftps":
            use_ssl = True
        self.use_ssl = use_ssl

        self.client = pycurl.Curl()
        self._reset()

    def _reset(self):
        """Reset pycurl internal client options to it's original/default state"""
        self.client.reset()
        if self.use_ssl:
            self.client.setopt(pycurl.USE_SSL, True)
            self.client.setopt(pycurl.SSL_VERIFYPEER, False)
            self.client.setopt(pycurl.SSL_VERIFYHOST, False)
        self.client.setopt(pycurl.CONNECTTIMEOUT, self.connect_timeout)
        if self.username and self.password:
            self.client.setopt(pycurl.USERPWD, f"{self.username}:{self.password}")

    def _perform(self):
        """Perform operation with retries."""
        attempt = 0
        while True:
            try:
                self.client.perform()
                return True
            except pycurl.error:
                attempt += 1
                if attempt >= self.max_retries:
                    raise

    def mlsd(self, remote_dir: typing.Union[None, str] = None):
        """List files in remote directory using the mlsd command."""
        if remote_dir is None:
            # List root directory by default
            remote_dir = ""
        elif not remote_dir.endswith("/"):
            # Make sure that directory ends with a forward slash character
            remote_dir += "/"

        url = urljoin(self.base_url, remote_dir)
        self.client.setopt(pycurl.URL, url)

        output_buffer = io.BytesIO()
        self.client.setopt(pycurl.WRITEDATA, output_buffer)
        self.client.setopt(pycurl.CUSTOMREQUEST, "MLSD %s" % (remote_dir))

        self._perform()
        self._reset()

        output = output_buffer.getvalue().decode("utf-8")
        for line in output.splitlines():
            facts_found, _, name = line.partition(" ")
            name = os.path.join(remote_dir, name)
            entry = {}
            for fact in facts_found[:-1].split(";"):
                key, _, value = fact.partition("=")
                entry[key.lower()] = value
            yield (name, entry)

    def list(self, remote_dir: typing.Union[None, str] = None):
        """
        List files in remote directory.
        Please ideally use mlsd instead.
        """

        warnings.warn(
            "List is not recommended, please us mlsd instead, unless"
            " absolutely necessary. The LIST command is not consistent across"
            " FTP servers, nor it standardised. However MLSD is relatively"
            ' "modern" and may not supported.',
            DeprecationWarning,
            stacklevel=2,
        )

        if remote_dir is None:
            # List root directory by default
            remote_dir = ""
        elif not remote_dir.endswith("/"):
            # Make sure that directory ends with a forward slash character
            remote_dir += "/"

        url = urljoin(self.base_url, remote_dir)
        self.client.setopt(pycurl.URL, url)

        output_buffer = io.BytesIO()
        self.client.setopt(pycurl.WRITEDATA, output_buffer)
        self._perform()
        self._reset()

        output = output_buffer.getvalue().decode("utf-8")

        parser = ftpparser.FTPParser()
        for line in output.splitlines():
            filename = parser.parse([line])
            file = os.path.join(remote_dir, filename[0][0])
            yield (file, False)

    def download(self, remote_filename: str, handle: typing.IO[bytes]):
        """Download remote file and write to handle"""
        url = urljoin(self.base_url, remote_filename)
        self.client.setopt(pycurl.URL, url)

        self.client.setopt(pycurl.WRITEDATA, handle)
        self._perform()
        self._reset()

    def upload(self, handle: typing.IO[bytes], remote_filename: str):
        """Upload handle (file or file-like) to server."""
        url = urljoin(self.base_url, remote_filename)
        self.client.setopt(pycurl.URL, url)

        self.client.setopt(pycurl.UPLOAD, True)
        self.client.setopt(pycurl.READDATA, handle)
        self._perform()
        self._reset()

    def _raw(self, command: str):
        """Send raw command to server."""
        self.client.setopt(pycurl.URL, self.base_url)
        self.client.setopt(pycurl.QUOTE, [command])
        self.client.setopt(pycurl.WRITEFUNCTION, lambda x: None)
        self._perform()
        self._reset()

    def delete(self, remote_filename: str):
        """Delete remote file."""
        self._raw("DELE %s" % (remote_filename))

    def mkd(self, remote_dir: str):
        """Create remote directory."""
        self._raw("MKD %s" % (remote_dir))

    def rmd(self, remote_dir: str):
        """Remove remote directory."""
        self._raw("RMD %s" % (remote_dir))

    def rename(self, from_remote_file: str, to_remote_file: str):
        """Rename remote file."""
        self._raw("RNFR %s" % (from_remote_file))
        self._raw("RNTO %s" % (to_remote_file))

    def exists(self, remote_filename: str):
        """Check if remote file exists."""
        dirname = os.path.dirname(remote_filename)
        name = os.path.basename(remote_filename)
        files = dict(self.mlsd(dirname))
        return name in files.keys() and files.get(name, {}).get("type", "") == "file"
