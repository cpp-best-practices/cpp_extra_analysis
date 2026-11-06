"""Type stubs for the `cppcheck` module that cppcheck provides to its addons at run time."""

from collections.abc import Callable
from typing import Any, TypeVar

_Checker = TypeVar("_Checker", bound=Callable[[Any, Any], None])

def checker(f: _Checker) -> _Checker: ...
def reportError(location: Any, severity: str, message: str, errorId: str | None = None) -> None: ...
