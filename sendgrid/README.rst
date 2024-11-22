========
sendgrid
========

Adds support for inbound email via SendGrid Inbound Parse.

Changelog
=========

- ⚠️ Under 15.0 support for "from address" rewriting has been removed, this is due to Odoo natively supporting this feature. Therefore `from_method` and `smtp_from_method` have been removed. You are expected to now either:

  - Use an intermediary SMTP server to rewrite the from address using SRS
  - Use the built in functionality - by setting the ir.config_parameters `mail.default.from`, or `mail.dynamic.smtp.from` and `mail.catchall.domain`

Usage
=====

- Install
- Setup SMTP as out of the box, either through configuration file or through UI
- Setup Sendgrid inbound parse to point to `https://odoo/sendgrid/inbound/databasename`

