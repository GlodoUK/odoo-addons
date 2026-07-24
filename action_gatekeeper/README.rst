Action Gatekeeper
=================
Gatekeeper to prevent actions or to trigger specific reactions based on defined rules.

On its own, this module does not do anything. It is meant to be used as a mixin for
other models.

e.g. see:
action_gatekeeper_sale

NOTE:
When creating an addon that uses this module, you will need to define your own views
to show gatekeeper holds, and decide what a gatekeeper hold means for your model.
