def test_list_notes(client):
    assert isinstance(client.list_notes(), list)
