from flask import Flask, jsonify, request

app = Flask(__name__)
BOOKS = [
    {"id": "1", "title": "On the Road", "author": "Jack Kerouac", "read": True},
    {"id": "2", "title": "Dune", "author": "Frank Herbert", "read": False},
]


@app.route("/books", methods=["GET", "POST"])
def books():
    if request.method == "POST":
        BOOKS.append(request.get_json())
        return jsonify({"status": "success", "books": BOOKS})
    selected = request.args.get("read")
    values = BOOKS
    if selected in {"true", "false"}:
        expected = selected == "true"
        values = [book for book in BOOKS if book["read"] is expected]
    return jsonify({"status": "success", "books": values})


@app.route("/books/<book_id>", methods=["PUT", "DELETE"])
def book(book_id):
    current = next(book for book in BOOKS if book["id"] == book_id)
    if request.method == "PUT":
        current.update(request.get_json())
    else:
        BOOKS.remove(current)
    return jsonify({"status": "success", "book": current})
