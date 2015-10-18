import json
from aiohttp.web import Response


class JSONResponse(Response):
    def __init__(self, body=None,
                 content_type='application/json; charset=utf-8',
                 **kwargs):
        if body is None:
            body = {}
        if isinstance(body, dict):
            body = json.dumps(body).encode()
        super().__init__(body=body, content_type=content_type, **kwargs)
