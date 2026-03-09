# Graph Bar Chart Zero Fill

## The Problem

When using bar charts in Odoo reporting grouped by date, any days with no results are
silently skipped. The chart jumps from one date with data straight to the next, making
it look like there are no gaps. This is misleading when filtering reports for specific
brand, products etc. where zero-value days are meaningful.

Line charts do not have this problem - they always show every day in the range.

## What This Module Does

Bar charts now display all dates in the range, including days with zero values. This
matches how line charts already behave
