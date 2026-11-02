#!/usr/bin/env python3
"""Flags std::endl; stream '\\n' instead and flush explicitly when required."""

import cppcheck


def is_std_endl(token):
    scope = token.previous
    return (
        token.str == "endl"
        and scope is not None
        and scope.str == "::"
        and scope.previous is not None
        and scope.previous.str == "std"
    )


@cppcheck.checker
def stdEndl(cfg, data):
    for token in filter(is_std_endl, cfg.tokenlist):
        cppcheck.reportError(
            token,
            "performance",
            "std::endl flushes the stream; prefer '\\n' and flush explicitly when required",
        )
