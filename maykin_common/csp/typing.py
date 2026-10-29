from __future__ import annotations

type DirectiveMapping = dict[str, list[str]]
"""
A mapping of CSP directive names to the list of sources configured for them.

The keys are the raw directive names as used by django-csp, e.g. ``"img-src"``.
"""
