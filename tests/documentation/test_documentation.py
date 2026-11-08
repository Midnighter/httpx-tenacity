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


"""
Test code examples in documentation.

We assume that examples in the documentation are at a similar level as acceptance tests.
Every Python code block of `README.md` and `docs/**/*.md` runs on its own as a complete
script in a fresh namespace, so each block has to restate its imports. Asynchronous
examples run themselves with `anyio.run(main)`, which is why the test is synchronous.

The `HTTPTransport` and `AsyncHTTPTransport` of HTTPX and HTTPX2 are replaced by
factories that return that client's `MockTransport` answering 200, so that no example
touches the network. The factories bind their arguments to the signature of the real
transport, so that documented options which the real transport does not accept fail the
test.

"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import httpx2
import pytest
from mktestdocs import grab_code_blocks


if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable
    from types import ModuleType


ROOT_DIR = Path(__file__).parents[2]
DOCS = sorted([*(ROOT_DIR / "docs").glob("**/*.md"), ROOT_DIR / "README.md"])
EXAMPLES = [
    pytest.param(
        block,
        id=f"{document.relative_to(ROOT_DIR).as_posix()}::{index}",
    )
    for document in DOCS
    for index, block in enumerate(grab_code_blocks(document.read_text()))
]


def _mock_transport_factory(
    client: ModuleType,
    transport_class: type[object],
) -> Callable[..., object]:
    """Create a replacement for a network transport of a client that answers 200."""
    signature = inspect.signature(transport_class)

    def factory(*args: object, **kwargs: object) -> object:
        # Binding the arguments rejects those that the real transport does not take.
        signature.bind(*args, **kwargs)
        return client.MockTransport(
            lambda request: client.Response(200, request=request),
        )

    return factory


@pytest.fixture
def mock_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the network transports of HTTPX and HTTPX2 with mock transports."""
    for client in (httpx, httpx2):
        for name in ("HTTPTransport", "AsyncHTTPTransport"):
            monkeypatch.setattr(
                client,
                name,
                _mock_transport_factory(client, getattr(client, name)),
            )


@pytest.mark.usefixtures("mock_network")
@pytest.mark.parametrize("block", EXAMPLES)
def test_document_examples_independently(block: str):
    """
    Run an individual code example from a document.

    Each code block must be completely independent of each other, for example, imports
    must be restated within each block. Asynchronous examples run themselves.

    """
    exec(block, {"__name__": "__main__"})  # noqa: S102
