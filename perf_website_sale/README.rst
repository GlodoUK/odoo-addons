=================
perf_website_sale
=================

A collection of performance improvements for website_sale under 18.0.

This includes some partial backports from unreleased 19.0.

This includes some indexes which are only appropriate for installations with larger numbers of product templates and product variants.

:warning: Pair this with appropriate PostgreSQL configuration, for example `random_io_cost` left at default on SSDs will result in extremely sub-optimal query plans even with this module.

