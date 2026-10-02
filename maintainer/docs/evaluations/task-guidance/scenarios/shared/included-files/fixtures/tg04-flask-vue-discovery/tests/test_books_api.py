def test_books(client):
    response = client.get("/books")
    assert response.status_code == 200


def test_book_mutations(client):
    created = client.post(
        "/books",
        json={"id": "3", "title": "Kindred", "author": "Octavia Butler", "read": False},
    )
    assert created.status_code == 200
    assert client.put("/books/3", json={"read": True}).status_code == 200
    assert client.delete("/books/3").status_code == 200
