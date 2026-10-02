def test_read_all_notes(test_app):
    response = test_app.get("/notes/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_crud_routes_exist(test_app):
    assert test_app.post("/notes/", json={"title": "abc", "description": "def"}).status_code == 201
