from webob import Request, Response
from parse import parse


class API:
    def __init__(self) -> None:
        self.routes = {}

    def __call__(self, environ, start_response):
        request = Request(environ)

        response = self.handle_request(request)
        return response(environ, start_response)

    def default_response(self, response):
        response.status_code = 404
        response.text = "Not found."

    def route(self, path):
        assert path not in self.routes, f"multiple routes with same path={path} "

        def wrapper(handler):
            self.routes[path] = handler
            return handler

        return wrapper

    def find_handler(self, request: Request):
        for path, handler in self.routes.items():
            parsed_result = parse(path, request.path)
            if parsed_result is not None:
                return handler, parsed_result.named

        return None, None

    def handle_request(self, request: Request) -> Response:
        response = Response()
        handler, path_kwargs = self.find_handler(request)
        if handler:
            handler(request, response, **path_kwargs)
        else:
            self.default_response(response)
        return response
