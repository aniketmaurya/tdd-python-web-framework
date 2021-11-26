"""
According to PEP 333, the document which specifies the details of WSGI,
the application interface is implemented as a callable object such as a function,
a method, a class, or an instance with a __call__ method.
This object should accept two positional arguments and return the response body as
strings in an iterable.

The two arguments are:

- a dictionary with environment variables
- a callback function that will be used to send HTTP
statuses and HTTP headers to the server
"""

from wsgiref.simple_server import make_server


class Reverseware:
    def __init__(self, app):
        self.wrapped_app = app

    def __call__(self, environ, start_response, *args, **kwargs):
        wrapped_app_response = self.wrapped_app(environ, start_response)
        return [data[::-1] for data in wrapped_app_response]


def application(environ, start_response):
    response_body = [f"{key}: {value}" for key, value in sorted(environ.items())]
    response_body = "\n".join(response_body)

    status = "200 OK"
    response_headers = [
        ("Content-type", "text/plain"),
    ]
    start_response(status, response_headers)

    return [response_body.encode("utf-8")]


server = make_server("localhost", 8000, app=Reverseware(application))
server.serve_forever()
