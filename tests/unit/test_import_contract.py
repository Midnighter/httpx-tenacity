# Copyright (c) 2026 Moritz E. Beber
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.


"""Test which HTTP clients the package and its integrations import."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap

import pytest


CORE_MODULES = (
    "httpx_tenacity",
    "httpx_tenacity.retry_policy",
    "httpx_tenacity.wait",
    "httpx_tenacity.retry_callback",
)
HTTP_CLIENTS = ("httpx", "httpx2")
INTEGRATION_MODULES = tuple(f"httpx_tenacity.{client}" for client in HTTP_CLIENTS)

# Each run starts a fresh interpreter that imports a single module and reports what
# that import loaded or how it failed. Blocked HTTP clients cannot be imported, as if
# they were not installed. Failing HTTP clients raise a `ModuleNotFoundError` for one
# of their own dependencies instead, as if that dependency were not installed.
SCRIPT = textwrap.dedent(
    """
    import importlib
    import importlib.abc
    import json
    import sys

    module, blocked, failing = json.loads(sys.argv[1])

    for name in blocked:
        sys.modules[name] = None


    class FailingFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname in failing:
                raise ModuleNotFoundError(
                    "No module named 'httpcore'", name="httpcore"
                )
            return None


    sys.meta_path.insert(0, FailingFinder())

    try:
        importlib.import_module(module)
    except ModuleNotFoundError as error:
        outcome = {"error": str(error), "name": error.name}
    else:
        loaded = sorted(m for m in ("httpx", "httpx2") if sys.modules.get(m))
        outcome = {"loaded": loaded}
    print(json.dumps(outcome))
    """,
)


def import_in_fresh_interpreter(
    module: str,
    blocked: tuple[str, ...] = (),
    failing: tuple[str, ...] = (),
) -> dict[str, object]:
    """
    Import a module in a fresh interpreter.

    Args:
        module: The name of the module to import.
        blocked: The HTTP clients that are not installed.
        failing: The HTTP clients whose import fails with a missing dependency.

    Returns:
        The names of the HTTP clients that the import loaded, or the message and
        name of the `ModuleNotFoundError` that it raised.

    """
    return json.loads(
        subprocess.run(  # noqa: S603
            [sys.executable, "-c", SCRIPT, json.dumps([module, blocked, failing])],
            capture_output=True,
            text=True,
            check=True,
        ).stdout,
    )


@pytest.mark.parametrize(
    "blocked",
    [(), ("httpx",), ("httpx2",), ("httpx", "httpx2")],
    ids=["none-blocked", "httpx-blocked", "httpx2-blocked", "both-blocked"],
)
@pytest.mark.parametrize("module", [*CORE_MODULES, *INTEGRATION_MODULES])
def test_import_contract(module: str, blocked: tuple[str, ...]):
    """Test that each import loads exactly the HTTP clients that it needs."""
    outcome = import_in_fresh_interpreter(module, blocked)

    client = module.removeprefix("httpx_tenacity.")
    if client not in HTTP_CLIENTS:
        # The core modules import no HTTP client.
        assert outcome == {"loaded": []}
    elif client in blocked:
        assert outcome["name"] == client
        assert f"httpx-tenacity[{client}]" in str(outcome["error"])
    else:
        # An integration loads its own client and never the other one, even when the
        # other integration has not been imported first.
        assert outcome == {"loaded": [client]}


@pytest.mark.parametrize("client", HTTP_CLIENTS)
def test_transitive_import_error_propagates(client: str):
    """Test that a missing dependency of an HTTP client is not hidden."""
    outcome = import_in_fresh_interpreter(
        f"httpx_tenacity.{client}",
        failing=(client,),
    )

    assert outcome == {
        "error": "No module named 'httpcore'",
        "name": "httpcore",
    }
