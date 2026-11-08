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


"""Test httpx-tenacity's compatibility with Pyodide."""

import pytest
from pytest_pyodide import run_in_pyodide
from pytest_pyodide.decorator import copy_files_to_pyodide


DISTRIBUTION_PATHS = [
    ("dist/", "dist/"),
]


@pytest.mark.parametrize("backend", ["httpx", "httpx2"])
@copy_files_to_pyodide(
    file_list=DISTRIBUTION_PATHS,
    install_wheels=True,
    recurse_directories=False,
)
@run_in_pyodide(packages=["micropip"])
async def test_async_tenacious_transport(selenium_standalone, backend):  # noqa: ARG001, ANN001
    """Test that an asynchronous tenacious transport retries in Pyodide."""
    from importlib import import_module
    from importlib.metadata import version

    # We need to replicate optional dependency installation in Pyodide,
    # unfortunately, since we cannot specify extras during the wheel installation.
    import micropip

    await micropip.install(
        [
            {"httpx": "httpx ~=0.25", "httpx2": "httpx2 ~=2.10"}[backend],
            "tenacity ~=9.1",
        ],
    )

    import tenacity
    from httpx_tenacity import SmartRetryPolicy

    http = import_module(backend)
    integration = import_module(f"httpx_tenacity.{backend}")
    if backend == "httpx2":
        # On Emscripten, httpx2 replaces httpcore2 and anyio with httpx2-jsfetch.
        assert version("httpx2-jsfetch")

    calls = []

    def handler(request):  # noqa: ANN001, ANN202
        calls.append(request)
        return http.Response(500, text="Server Error")

    async with http.AsyncClient(
        transport=integration.AsyncTenaciousTransport.create(
            policy=SmartRetryPolicy(max_attempts=3, max_wait_seconds=0.1),
            transport=http.MockTransport(handler=handler),
        ),
    ) as client:
        try:
            await client.get("http://example.com")
        except tenacity.RetryError:
            pass
        else:
            msg = "The request did not end in a RetryError."
            raise AssertionError(msg)

    assert len(calls) == 3


@pytest.mark.parametrize("backend", ["httpx", "httpx2"])
@copy_files_to_pyodide(
    file_list=DISTRIBUTION_PATHS,
    install_wheels=True,
    recurse_directories=False,
)
@run_in_pyodide(packages=["micropip"])
async def test_tenacious_transport(selenium_standalone, backend):  # noqa: ARG001, ANN001
    """Test that a synchronous tenacious transport retries in Pyodide."""
    from importlib import import_module

    # We need to replicate optional dependency installation in Pyodide,
    # unfortunately, since we cannot specify extras during the wheel installation.
    import micropip

    await micropip.install(
        [
            {"httpx": "httpx ~=0.25", "httpx2": "httpx2 ~=2.10"}[backend],
            "tenacity ~=9.1",
        ],
    )

    import tenacity
    from httpx_tenacity import SmartRetryPolicy

    http = import_module(backend)
    integration = import_module(f"httpx_tenacity.{backend}")

    calls = []

    def handler(request):  # noqa: ANN001, ANN202
        calls.append(request)
        return http.Response(500, text="Server Error")

    with http.Client(
        transport=integration.TenaciousTransport.create(
            policy=SmartRetryPolicy(max_attempts=3, max_wait_seconds=0.1),
            transport=http.MockTransport(handler=handler),
        ),
    ) as client:
        try:
            client.get("http://example.com")
        except tenacity.RetryError:
            pass
        else:
            msg = "The request did not end in a RetryError."
            raise AssertionError(msg)

    assert len(calls) == 3
