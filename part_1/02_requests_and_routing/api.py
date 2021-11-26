import inspect
import os

from jinja2 import Environment, FileSystemLoader
from parse import parse
from requests import Session as RequestsSession
from webob import Request, Response
from wsgiadapter import WSGIAdapter as RequestsWSGIAdapter


class API:
    def __init__(self, template_dir="templates") -> None:
        self.routes = {}
        self.templates_env = Environment(
            loader=FileSystemLoader(os.path.abspath(template_dir))
        )

    def template(self, template_name, context=None):
        if context is None:
            context = {}
        return self.templates_env.get_template(template_name).render(**context)

    def __call__(self, environ, start_response):
        request = Request(environ)

        response = self.handle_request(request)
        return response(environ, start_response)

    def default_response(self, response):
        response.status_code = 404
        response.text = "Not found."

    def add_route(self, path, handler):
        assert path not in self.routes, f"multiple routes with same path={path} "
        self.routes[path] = handler

    def route(self, path):
        def wrapper(handler):
            self.add_route(path, handler)
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
        if inspect.isclass(handler):
            handler = getattr(handler(), request.method.lower(), None)
            if handler is None:
                raise AttributeError("Method not allowed", request.method)
        if handler:
            handler(request, response, **path_kwargs)
        else:
            self.default_response(response)
        return response

    def test_session(self, base_url="http://testserver"):
        session = RequestsSession()
        session.mount(prefix=base_url, adapter=RequestsWSGIAdapter(self))
        return session
