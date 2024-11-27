--------------------------
connector_edi_protocol_ssh
--------------------------

Implements SFTP and SCP Client as a protocol through the packages `paramiko` and `scp`.

Installation
------------

You will need to install pycurl, which may need to be built from source.

If you are using doodba you need to:

1. Add paramiko and scp to pip.txt
2. Rebuild your image (after stopping any running containers)

Known Issues
------------

* Lack of unit tests
* Does not support directory globs (i.e. `/**/*.txt`, but `/In/*.txt` is
  supported)
