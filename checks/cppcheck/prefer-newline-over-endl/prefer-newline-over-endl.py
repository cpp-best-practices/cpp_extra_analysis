#!/usr/bin/env python3
"""Flags std::endl; stream '\\n' instead and flush explicitly when required."""

from typing import Any

import cppcheck


def is_std_endl(token: Any) -> bool:
    scope = token.previous
    return (
        token.str == "endl"
        and scope is not None
        and scope.str == "::"
        and scope.previous is not None
        and scope.previous.str == "std"
    )


@cppcheck.checker
def stdEndl(cfg: Any, data: Any) -> None:
    for token in filter(is_std_endl, cfg.tokenlist):
        cppcheck.reportError(
            token,
            "performance",
            "std::endl flushes the stream; prefer '\\n' and flush explicitly when required",
        )
