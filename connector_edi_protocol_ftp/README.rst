--------------------------
connector_edi_protocol_ftp
--------------------------

Implements FTP Client as a protocol through pycurl.

PyCurl is used to avoid numerous issues with ftplib, which ships with Python and
various FTP servers, such as:

 * https://bugs.python.org/issue10808
 * https://bugs.python.org/issue19500


Installation
------------

You will need to install pycurl, which may need to be built from source.

If you are using doodba you need to:

1. Add pycurl to pip.txt
2. Add libcurl4-openssl-dev, libssl-dev and build-essential to apt_build.txt
3. Rebuild your image (after stopping any running containers)

Known Issues
------------

* Lack of unit tests
* Missing does not use FEAT commands to determine if features like MLSD or LIST
  are supported.
* Does not support directory globs (i.e. `/**/*.txt`, but `/In/*.txt` is
  supported)
* FTP client needs better support for checking previous command worked without
  throwing exceptions left right and center.
