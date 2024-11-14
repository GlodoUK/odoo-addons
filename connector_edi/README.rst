=============
connector_edi
=============

This module describes some high level primitives for basic EDI.

edi.backend - A collection of routes edi.route - A description of how to;

1. collect envelopes, how to decode envelopes into messages and then process those messages
2. create messages, encode one or more messages into an envelope and then send those envelopes edi.envelope - A collection of 1 or more messages edi.message - An EDI message

Future Development Considerations
---------------------------------

Fundamentally there is no longer really a reason why both `edi.envelope` and
`edi.message` both need to exist:

1. It would be great if we can merge the two models together.
2. This would naturally lead onto the merge of `edi.envelope.route` and `edi.message.route`.
3. This then means that we can allow arbitrary number of steps (think sink and source)

:warning: If this were to be carried out it is imperative that no data is lost.

