=============
connector_edi
=============

This module describes some high level primitives for basic EDI.

edi.backend - A collection of routes edi.route - A description of how to;

1. collect envelopes, how to decode envelopes into messages and then process those
   messages
2. create messages, encode one or more messages into an envelope and then send those
   envelopes edi.envelope - A collection of 1 or more messages edi.message - An EDI
   message

