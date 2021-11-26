from api import API

app = API()


@app.route("/home")
def home(request, response):
    response.text = "Hello from the HOME page"


@app.route("/about")
def about(request, response):
    response.text = "Hello from the ABOUT page"


@app.route("/hello/{name}")
def greeting(request, response, name):
    response.text = f"Hello, {name}"


@app.route("/sum/{num_1:d}/{num_2:d}")
def sum(request, response, num_1, num_2):
    total = int(num_1) + int(num_2)
    response.text = f"{num_1} + {num_2} = {total}"


@app.route("/book")
class BooksResource:
    def get(self, req, resp):
        resp.text = "Books Page"

    def post(self, req, resp):
        resp.text = "Endpoint to create a book"


def yolo(req, resp):
    resp.text = "YOLO"


def yolo1(req, resp):
    resp.text = "YOLO1"


app.add_route("/yolo", yolo)
app.add_route("/yolo1", yolo1)


@app.route("/template")
def template_handler(request, response):
    response.body = app.template(
        "index.html", context={"name": "Bumbo", "title": "Best Framework"}
    ).encode()


# Expcetption handling for path not found
def custom_exception_handler(req, resp, exc):
    resp.text = str(exc)


app.add_exception_handler(custom_exception_handler)
