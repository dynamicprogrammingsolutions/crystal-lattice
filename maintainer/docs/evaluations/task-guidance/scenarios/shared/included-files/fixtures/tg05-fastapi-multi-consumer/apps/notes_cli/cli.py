import argparse
from notes_client.client import NotesClient


def list_command(client):
    for note in client.list_notes():
        print(f"{note['id']}: {note['title']}")


def main(argv=None, client=None):
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("list")
    args = parser.parse_args(argv)
    selected = client or NotesClient.from_environment()
    if args.command == "list":
        list_command(selected)
