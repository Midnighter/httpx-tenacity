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

import tenacity
from pytest_pyodide import run_in_pyodide
from pytest_pyodide.decorator import copy_files_to_pyodide


DISTRIBUTION_PATHS = [
    ("dist/", "dist/"),
]


@copy_files_to_pyodide(
    file_list=DISTRIBUTION_PATHS,
    install_wheels=True,
    recurse_directories=False,
)
@run_in_pyodide(packages=["httpx", "tenacity"])
async def test_async_tenacious_transport(selenium_standalone):  # noqa: ARG001, ANN001
    """Test that we can import and use an asynchronous tenacious transport."""
    import httpx
    from httpx_tenacity import AsyncTenaciousTransport

    async with httpx.AsyncClient(
        transport=AsyncTenaciousTransport.create(
            max_attempts=3,
            max_wait_seconds=0.1,
        ),
    ) as client:
        try:
            await client.get("https://httpbin.org/status/500")
        except tenacity.RetryError:
            pass
