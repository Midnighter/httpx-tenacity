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
Provide the retry policies that configure the tenacious transports.

This package imports no HTTP client. The transports live in the integration
packages, `httpx_tenacity.httpx` for HTTPX and `httpx_tenacity.httpx2` for
HTTPX2. Each of them requires its own extra.

"""

from .retry_policy import RetryingT, RetryPolicy, SmartRetryPolicy
