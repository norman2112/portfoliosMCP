"""Proxy response utilities for proxy services."""


def chunk_params(params, n):
    """Break params into chunks of at most n elements."""

    chunks = []
    for i in range(0, len(params), n):
        chunks.append(params[i : i + n])

    return chunks


async def merge_chunks(chunked_responses):
    """Merge chunks of dicts with same keys."""
    if not chunked_responses:
        return {}
    result = await chunked_responses[0].json()
    for chunk in chunked_responses[1:]:
        resp = await chunk.json()
        for k in resp:
            if isinstance(result.get(k), list):
                result[k] = result[k] + resp[k]
    return result


class ChunkedResponse:
    """Wrap a bunch of chunked responses."""

    def __init__(self, responses=None):
        """Initialize a chunked response object."""

        if responses is None:
            self._responses = []
        else:
            self._responses = responses

    @property
    def responses(self):
        """Return the wrapped responses."""

        return self._responses


def _is_chunked_response(resp):
    return isinstance(resp, ChunkedResponse)


class ProxyResponseWrapper:
    """
    Wrap aiohttp.clientResponses sent to the service wrangler.

    This wrapper takes in one or multiple aiohttp client responses from the
    service proxies. This is useful when multiple API requests are needed to
    scrape together the requisite amount of data the adapter needs.
    """

    def __init__(self, response):
        """
        Initialize the ProxyResponseWrapper.

        param (ClientResponse | dict) response: either a single
         AioHttp ClientResponse or a dict of keyed ClientResponses.

        ::Example of a multi-response dict::

          {
            "board_detail": <ClientResponse>,
            "card_detail": <ClientResponse>
          }

        Docs on Aiohttp.ClientResponse object here:
        https://docs.aiohttp.org/en/stable/client_reference.html#response-object
        """
        self.response = response

    def request_urls(self):
        """Return the request urls for all responses."""

        return [
            str(response.responses[0].request_info.url)
            if _is_chunked_response(response)
            else str(response.request_info.url)
            for response in self._all_responses()
        ]

    async def response_data(self):
        """
        Return the response data for all proxy_responses passed in.

        If the incoming self.response is a multi-response, or chunked response then create a new
        dict of json response data, set to the keys provided in the original
        dict.
        """

        if _is_chunked_response(self.response):
            return await merge_chunks(self.response.responses)
        if self._is_multi_response():
            response_dict = {}
            for key, resp in self.response.items():
                if _is_chunked_response(resp):
                    response_dict[key] = await merge_chunks(resp.responses)
                else:
                    response_dict[key] = await resp.json()
            return response_dict
        return await self.response.json()

    def statuses(self):
        """Return all statuses of all responses."""
        all_statues = []

        for response in self._all_responses():
            if _is_chunked_response(response):
                for ch_response in response.responses:
                    all_statues.append(ch_response.status)
            else:
                all_statues.append(response.status)

        return all_statues

    def status_to_return(self):
        """
        Return one of the statuses from the requests.

        If the status is in error, then report the first error. Otherwise,
        return the first ok status.
        """
        all_statuses = self.statuses()
        for status in all_statuses:
            if status >= 300:
                return status

        return all_statuses[0]

    def ok(self):
        """Return True if all responses were `ok`."""
        for response in self._all_responses():
            if _is_chunked_response(response):
                for resp in response.responses:
                    if not resp.ok:
                        return False
            elif not response.ok:
                return False

        return True

    def reasons(self):
        """Return amalgamated reasons from the requests."""
        reasons = [
            response.reason
            for response in self._all_responses()
            if hasattr(response, "reason")
        ]
        return " | ".join(reasons)

    def _is_multi_response(self):
        return isinstance(self.response, dict)

    def _all_responses(self):
        if self._is_multi_response():
            return self.response.values()

        return [self.response]
