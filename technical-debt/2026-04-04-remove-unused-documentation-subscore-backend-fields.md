# Technical Debt

## Description

The HTML tables on the home page and venue summary pages no longer render the documentation median, dataset, code, and other documentation columns, but the backend still fetches and passes those values through to the templates.

## Solution

Remove the unused datastore, viewmodel, and template-support fields for the documentation median and the dataset, code, and other documentation subscores once the UI decision is confirmed as permanent. Remove any dead sorting or data-attribute plumbing tied to those values at the same time.

## Impact

Removing the unused backend support will reduce dead code paths and maintenance overhead without changing visible behavior.
