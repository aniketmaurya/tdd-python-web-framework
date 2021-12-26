import inspect
import os
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader
from middleware import Middleware
from parse import parse
from requests import Session as RequestsSession
from webob import Request, Response
from whitenoise import WhiteNoise
from wsgiadapter import WSGIAdapter as RequestsWSGIAdapter


class API:
    """
    - WhiteNoise is used for serving static dir.
    """

    def __init__(self, templates_dir="templates", static_dir="static"):
        self.routes = {}
        self.exception_handler = None
        self.templates_env = Environment(
            loader=FileSystemLoader(os.path.abspath(templates_dir))
        )
        self.whitenoise = WhiteNoise(self.wsgi_app, root=static_dir)
        self.middleware = Middleware(self)

    def __call__(self, environ, start_response):
        path_info = environ["PATH_INFO"]
        if path_info.startswith("/static"):
            environ["PATH_INFO"] = path_info[len("/static") :]
            return self.whitenoise(environ, start_response)
        return self.middleware(environ, start_response)

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response: Response = self.handle_request(request)
        return response(environ, start_response)

    def default_response(self, response):
        response.status_code = 404
        response.text = "Not found."

    def add_route(self, path, handler, allowed_methods=None):
        assert path not in self.routes, f"multiple routes with same path={path} "
        if allowed_methods is None:
            allowed_methods = ["get", "post", "put", "patch", "delete", "options"]
        self.routes[path] = {"handler": handler, "allowed_methods": allowed_methods}

    def route(self, path, allowed_methods: Optional[List[str]] = None):
        def wrapper(handler):
            self.add_route(path, handler, allowed_methods)
            return handler

        return wrapper

    def find_handler(self, request: Request):
        for path, handler_data in self.routes.items():
            parsed_result = parse(path, request.path)
            if parsed_result is not None:
                return handler_data, parsed_result.named

        return None, None

    def handle_request(self, request: Request) -> Response:
        response = Response()

        handler_data, path_kwargs = self.find_handler(request)

        try:
            if handler_data is not None:
                handler = handler_data["handler"]
                allowed_methods = handler_data["allowed_methods"]
                if inspect.isclass(handler):
                    handler = getattr(handler(), request.method.lower(), None)
                    if handler is None:
                        raise AttributeError("Method not allowed", request.method)
                else:
                    if request.method.lower() not in allowed_methods:
                        raise AttributeError("Method not allowed", request.method)

                handler(request, response, **path_kwargs)
            else:
                self.default_response(response)

        except Exception as e:
            if self.exception_handler is None:
                raise e
            else:
                self.exception_handler(request, response, e)
        return response

    def test_session(self, base_url="http://testserver"):
        session = RequestsSession()
        session.mount(prefix=base_url, adapter=RequestsWSGIAdapter(self))
        return session

    def add_exception_handler(self, exc_handler):
        self.exception_handler = exc_handler

    def template(self, template_name, context=None):
        if context is None:
            context = {}
        return self.templates_env.get_template(template_name).render(**context)

    def add_middleware(self, middleware_cls):
        self.middleware.add(middleware_cls)
