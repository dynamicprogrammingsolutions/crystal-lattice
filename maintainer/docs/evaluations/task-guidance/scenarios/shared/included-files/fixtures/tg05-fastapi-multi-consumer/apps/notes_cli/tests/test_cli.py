def test_list_command(capsys, client):
    list_command(client)
    assert capsys.readouterr().out
