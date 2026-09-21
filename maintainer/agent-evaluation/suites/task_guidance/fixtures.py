from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from agent_eval.workspace import GitWorkspaceFactory, git_workspace
from maintainer.guidance import (
    bundle_section_path,
    compile_guidance,
    write_compilation,
)

from .scenarios import TaskGuidanceScenario


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
PACKAGE_ROOT = REPOSITORY_ROOT / "maintainer" / "agent-evaluation"
SUITE_ROOT = Path(__file__).resolve().parent
GUIDANCE_TARGET_ROOT = SUITE_ROOT / "fixtures" / "guidance"
DEFAULT_BUNDLE = REPOSITORY_ROOT / "maintainer" / "guidance" / "current"
BASE_REVISION = "094cf20fc4075188cf76a48c77a1d29a36ff0a78"
FIXTURE_VERSION = "v5"


COMMON_GITIGNORE = """\
__pycache__/
.pytest_cache/
node_modules/
_site/
"""


def selected_bundle() -> Path:
    raw = os.getenv("AGENT_EVAL_GUIDANCE_BUNDLE", "").strip()
    return Path(raw).expanduser().resolve() if raw else DEFAULT_BUNDLE


@dataclass(frozen=True)
class TaskGuidanceWorkspaceFactory:
    scenario: TaskGuidanceScenario
    bundle: Path
    revision: str = BASE_REVISION

    def fingerprint(self) -> object:
        compilation = compile_guidance(
            bundle=self.bundle,
            target=GUIDANCE_TARGET_ROOT / self.scenario.project_family,
            repository_root=REPOSITORY_ROOT,
        )
        return {
            "type": "task-guidance-fixture",
            "scenario_id": self.scenario.scenario_id,
            "fixture_id": self.scenario.fixture_id,
            "fixture_version": FIXTURE_VERSION,
            "base_revision": self.revision,
            "guidance_compilation_sha256": compilation.lock[
                "compilation_sha256"
            ],
        }

    def __call__(self, staging_dir: Path) -> Path:
        base = self._base()
        workspace = base(staging_dir)
        _write_fixture(workspace, self.scenario.fixture_id)
        compilation = compile_guidance(
            bundle=self.bundle,
            target=GUIDANCE_TARGET_ROOT / self.scenario.project_family,
            repository_root=REPOSITORY_ROOT,
        )
        write_compilation(compilation, destination=workspace)
        documentation_source = bundle_section_path(
            bundle=self.bundle,
            section="documentation",
            repository_root=REPOSITORY_ROOT,
        )
        documentation_target = (
            workspace / "docs" / "development" / "documentation.md"
        )
        documentation_target.parent.mkdir(parents=True, exist_ok=True)
        documentation_target.write_bytes(documentation_source.read_bytes())
        (workspace / ".guidance-lock.json").write_text(
            json.dumps(compilation.lock, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _commit_fixture(workspace)
        return workspace

    def cleanup(self, workspace: Path) -> None:
        self._base().cleanup(workspace)

    def _base(self) -> GitWorkspaceFactory:
        return git_workspace(
            source=REPOSITORY_ROOT,
            revision=self.revision,
            cache_root=PACKAGE_ROOT / ".repository-cache",
        )


@dataclass(frozen=True)
class AssessmentWorkspaceFactory:
    revision: str = BASE_REVISION

    def fingerprint(self) -> object:
        return {
            "type": "task-guidance-assessment",
            "fixture_version": FIXTURE_VERSION,
            "base_revision": self.revision,
        }

    def __call__(self, staging_dir: Path) -> Path:
        base = self._base()
        workspace = base(staging_dir)
        for path in workspace.iterdir():
            if path.name == ".git":
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        (workspace / "AGENTS.md").write_text(
            "# Evaluation workspace\n\n"
            "All material to assess is in the user message. Do not inspect or "
            "modify repository files.\n",
            encoding="utf-8",
        )
        (workspace / "README.md").write_text(
            "# Task-guidance semantic assessment\n",
            encoding="utf-8",
        )
        _commit_fixture(workspace)
        return workspace

    def cleanup(self, workspace: Path) -> None:
        self._base().cleanup(workspace)

    def _base(self) -> GitWorkspaceFactory:
        return git_workspace(
            source=REPOSITORY_ROOT,
            revision=self.revision,
            cache_root=PACKAGE_ROOT / ".repository-cache",
        )


def fixture_files(fixture_id: str) -> Mapping[str, str]:
    try:
        return FIXTURES[fixture_id]
    except KeyError as error:
        raise KeyError(f"unknown task-guidance fixture: {fixture_id}") from error


def _write_fixture(workspace: Path, fixture_id: str) -> None:
    for path in workspace.iterdir():
        if path.name == ".git":
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    files = {".gitignore": COMMON_GITIGNORE, **fixture_files(fixture_id)}
    for relative, content in files.items():
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content.rstrip() + "\n", encoding="utf-8")


def _commit_fixture(workspace: Path) -> None:
    _git(workspace, "add", "-A")
    _git(
        workspace,
        "-c",
        "user.name=Agent Evaluation",
        "-c",
        "user.email=agent-evaluation@example.invalid",
        "commit",
        "-m",
        "Prepare task guidance fixture",
    )


def _git(workspace: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(workspace), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git command failed: {args!r}\n{result.stdout}\n{result.stderr}"
        )
    return result.stdout


def fixture_sha256(fixture_id: str) -> str:
    payload = json.dumps(
        fixture_files(fixture_id),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


ELEVENTY_BASE = {
    "UPSTREAM.md": """\
# Upstream source

Compact fixture adapted from Eleventy Base Blog at
`26b26106d7fbb30b7b40d9ef52589d10ddbcb462`.
""",
    "README.md": """\
# Eleventy Base Blog

The production build creates a home page, blog archive, tag pages, feed,
sitemap, and individual posts without client-side JavaScript.
""",
    "package.json": """\
{
  "name": "task-guidance-eleventy-fixture",
  "type": "module",
  "scripts": {
    "build": "eleventy",
    "test": "node --test tests/*.test.js"
  },
  "devDependencies": {
    "@11ty/eleventy": "^3.0.0"
  }
}
""",
    "eleventy.config.js": """\
export default function(eleventyConfig) {
  eleventyConfig.addPassthroughCopy("public");
  eleventyConfig.addFilter("head", (values, count) =>
    count < 0 ? values.slice(count) : values.slice(0, count)
  );
  return {
    dir: {
      input: "content",
      includes: "../_includes",
      output: "_site"
    }
  };
}
""",
    "_includes/layouts/post.njk": """\
<h1>{{ title }}</h1>
<p class="author">{{ author }}</p>
{{ content | safe }}
""",
    "content/blog.njk": """\
---
permalink: /blog/
---
<h1>Archive</h1>
{% set postslist = collections.posts %}
{% include "postslist.njk" %}
""",
    "_includes/postslist.njk": """\
<ol class="postlist">
{% for post in postslist | reverse %}
  <li><a href="{{ post.url }}">{{ post.data.title }}</a></li>
{% endfor %}
</ol>
""",
    "content/index.njk": """\
{% set postslist = collections.posts | head(-3) %}
{% include "postslist.njk" %}
""",
    "content/tag-pages.njk": """\
---
pagination:
  data: collections
  size: 1
  alias: tag
  filter: [all, posts]
permalink: "/tags/{{ tag | slugify }}/"
---
{% set postslist = collections[tag] %}
{% include "postslist.njk" %}
""",
    "content/feed.xml.njk": """\
---
permalink: /feed/feed.xml
layout: false
---
<feed>{% for post in collections.posts | reverse %}<entry>{{ post.url }}</entry>{% endfor %}</feed>
""",
    "content/sitemap.xml.njk": """\
<urlset>{% for page in collections.all %}<url>{{ page.url }}</url>{% endfor %}</urlset>
""",
    "tests/archive-output.test.js": """\
// Production-build coverage currently checks only that /blog/index.html exists.
""",
    "content/posts/first.md": """\
---
title: First
date: 2026-01-01
tags: [posts]
---
First post.
""",
    "content/posts/second.md": """\
---
title: Second
date: 2026-01-02
tags: [posts]
---
Second post.
""",
    "content/posts/posts.json": """\
{
  "layout": "layouts/post.njk",
  "tags": ["posts"]
}
""",
    "docs/development/index.md": "# Development\n\nNo archive pagination specification exists.\n",
}


FASTAPI_BASE = {
    "UPSTREAM.md": """\
# Upstream source

Compact fixture adapted from FastAPI CRUD Async at
`4fa7ae952ece61e228135285de1b6a5ff65a1dc8`.
""",
    "README.md": """\
# FastAPI CRUD Async

The public notes API supports create, list, read, update, and delete. The
collection route currently returns every note as a JSON array.
""",
    "pyproject.toml": """\
[project]
name = "task-guidance-fastapi-fixture"
version = "0.1.0"
dependencies = [
  "databases[sqlite]",
  "fastapi",
  "httpx",
  "sqlalchemy",
]
""",
    "src/app/api/models.py": """\
from pydantic import BaseModel


class NoteCreate(BaseModel):
    title: str
    description: str


class Note(NoteCreate):
    id: int
""",
    "src/app/db.py": """\
import databases
import sqlalchemy

DATABASE_URL = "sqlite:///./notes.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
engine = sqlalchemy.create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
notes = sqlalchemy.Table(
    "notes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("title", sqlalchemy.String(50)),
    sqlalchemy.Column("description", sqlalchemy.String(50)),
)
metadata.create_all(engine)
""",
    "src/app/api/crud.py": """\
from app.db import database, notes


async def get_all():
    return await database.fetch_all(notes.select())


async def get(note_id):
    return await database.fetch_one(notes.select().where(notes.c.id == note_id))


async def post(payload):
    return await database.execute(notes.insert().values(**payload.model_dump()))


async def put(note_id, payload):
    await database.execute(
        notes.update().where(notes.c.id == note_id).values(**payload.model_dump())
    )
    return await get(note_id)


async def delete(note_id):
    note = await get(note_id)
    await database.execute(notes.delete().where(notes.c.id == note_id))
    return note
""",
    "src/app/api/notes.py": """\
from fastapi import APIRouter, HTTPException
from . import crud
from .models import NoteCreate

router = APIRouter()


@router.get("/")
async def read_all_notes():
    return await crud.get_all()


@router.get("/{note_id}/")
async def read_note(note_id: int):
    note = await crud.get(note_id)
    if note is None:
        raise HTTPException(status_code=404)
    return note


@router.post("/", status_code=201)
async def create_note(payload: NoteCreate):
    note_id = await crud.post(payload)
    return {"id": note_id, **payload.model_dump()}


@router.put("/{note_id}/")
async def update_note(note_id: int, payload: NoteCreate):
    return await crud.put(note_id, payload)


@router.delete("/{note_id}/")
async def delete_note(note_id: int):
    return await crud.delete(note_id)
""",
    "src/app/main.py": """\
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.notes import router
from app.db import database


@asynccontextmanager
async def lifespan(app):
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)
app.include_router(router, prefix="/notes")
""",
    "src/tests/conftest.py": """\
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def test_app():
    return TestClient(app)
""",
    "src/tests/test_notes.py": """\
def test_read_all_notes(test_app):
    response = test_app.get("/notes/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_crud_routes_exist(test_app):
    assert test_app.post("/notes/", json={"title": "abc", "description": "def"}).status_code == 201
""",
    "docs/development/index.md": "# Development\n\nNo notes-query specification exists.\n",
}


FLASK_VUE_BASE = {
    "UPSTREAM.md": """\
# Upstream source

Compact fixture adapted from Flask-Vue CRUD at
`be91da59a10d07384537c2f76f4505eb344d1682`.
""",
    "README.md": """\
# Flask-Vue CRUD

The Vue Books page loads and mutates books through the Flask JSON API.
""",
    "pyproject.toml": """\
[project]
name = "task-guidance-flask-vue-server"
version = "0.1.0"
dependencies = ["flask"]
""",
    "server/app.py": """\
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


@app.route("/books/<book_id>", methods=["PUT", "DELETE"])
def book(book_id):
    current = next(book for book in BOOKS if book["id"] == book_id)
    if request.method == "PUT":
        current.update(request.get_json())
    else:
        BOOKS.remove(current)
    return jsonify({"status": "success", "book": current})
""",
    "client/package.json": """\
{
  "name": "task-guidance-books-client",
  "type": "module",
  "scripts": {"test": "vitest run"},
  "dependencies": {
    "axios": "^1.7.0",
    "vue": "^3.5.0",
    "vue-router": "^4.4.0"
  },
  "devDependencies": {"@vue/test-utils": "^2.4.0", "vitest": "^2.1.0"}
}
""",
    "client/src/http.js": """\
import axios from "axios";

export const http = axios.create({ baseURL: "http://localhost:5000" });
""",
    "client/src/api/books.js": """\
import { http } from "../http";

export async function getBooks(params = {}) {
  return http.get("/books", { params });
}

export async function addBook(book) {
  return http.post("/books", book);
}

export const updateBook = (book) => http.put(`/books/${book.id}`, book);
export const deleteBook = (id) => http.delete(`/books/${id}`);
""",
    "client/src/components/Books.vue": """\
<template>
  <section>
    <table v-if="books.length">
      <tr v-for="book in books" :key="book.id">
        <td>{{ book.title }}</td>
        <td>{{ book.author }}</td>
      </tr>
    </table>
    <p v-else>No books found.</p>
  </section>
</template>

<script>
import { getBooks, addBook, updateBook, deleteBook } from "../api/books";

export default {
  data: () => ({ books: [] }),
  async mounted() { this.books = (await getBooks()).data.books; },
  methods: {
    async add(book) {
      await addBook(book);
      this.books = (await getBooks()).data.books;
    },
    async update(book) {
      await updateBook(book);
      this.books = (await getBooks()).data.books;
    },
    async remove(id) {
      await deleteBook(id);
      this.books = (await getBooks()).data.books;
    },
  },
};
</script>
""",
    "tests/conftest.py": """\
import pytest
from server.app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()
""",
    "tests/test_books_api.py": """\
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
""",
    "client/tests/Books.spec.js": """\
import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import Books from "../src/components/Books.vue";

vi.mock("../src/api/books", () => ({
  getBooks: vi.fn(async () => ({ data: { books: [] } })),
  addBook: vi.fn(),
  updateBook: vi.fn(),
  deleteBook: vi.fn(),
}));

describe("Books", () => {
  it("renders the empty state", async () => {
    const wrapper = mount(Books);
    await Promise.resolve();
    expect(wrapper.text()).toContain("No books found.");
  });
});
""",
    "docs/development/index.md": "# Development\n\nNo book-discovery specification exists.\n",
}


FIXTURES: dict[str, Mapping[str, str]] = {
    "tg01-eleventy-archive": ELEVENTY_BASE,
    "tg02-fastapi-pagination": FASTAPI_BASE,
    "tg03-flask-vue-refresh": {
        **FLASK_VUE_BASE,
        "server/app.py": """\
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
""",
        "client/src/components/Books.vue": """\
<template>
  <section>
    <nav aria-label="Book status filter">
      <button
        v-for="filter in ['all', 'read', 'unread']"
        :key="filter"
        :aria-pressed="selectedFilter === filter"
        @click="selectFilter(filter)"
      >
        {{ filter }}
      </button>
    </nav>
    <table v-if="books.length">
      <tr v-for="book in books" :key="book.id"><td>{{ book.title }}</td></tr>
    </table>
    <p v-else>No books found.</p>
  </section>
</template>

<script>
import { getBooks, addBook, updateBook, deleteBook } from "../api/books";

export default {
  data: () => ({ books: [], selectedFilter: "all" }),
  methods: {
    async selectFilter(value) {
      this.selectedFilter = value;
      this.books = (await getBooks(value)).data.books;
    },
    async add(book) {
      await addBook(book);
      this.books = (await getBooks()).data.books; // regression: filter lost
    },
    async update(book) {
      await updateBook(book);
      this.books = (await getBooks()).data.books; // regression: filter lost
    },
    async remove(id) {
      await deleteBook(id);
      this.books = (await getBooks()).data.books; // regression: filter lost
    },
  },
};
</script>
""",
        "client/src/api/books.js": """\
import { http } from "../http";

export async function getBooks(filter = "all") {
  const params = filter === "all" ? {} : { read: filter === "read" };
  return http.get("/books", { params });
}

export const addBook = (book) => http.post("/books", book);
export const updateBook = (book) => http.put(`/books/${book.id}`, book);
export const deleteBook = (id) => http.delete(`/books/${id}`);
""",
    },
    "tg04-flask-vue-discovery": {
        **FLASK_VUE_BASE,
        "server/query.py": """\
def list_books(books):
    return list(books)
""",
        "client/src/router.js": """\
import { createRouter, createWebHistory } from "vue-router";
import Books from "./components/Books.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: "/books", component: Books }],
});
""",
        "client/tests/books.integration.js": """\
// No production transport integration coverage exists yet.
""",
    },
    "tg05-fastapi-multi-consumer": {
        **FASTAPI_BASE,
        "packages/notes_client/README.md": """\
# notes-client

Reusable Python client for the notes service. `list_notes()` currently returns
the unparameterized collection.
""",
        "packages/notes_client/pyproject.toml": """\
[project]
name = "notes-client"
version = "0.1.0"
dependencies = ["httpx"]
""",
        "packages/notes_client/notes_client/client.py": """\
import os
import httpx


class NotesClient:
    def __init__(self, transport):
        self.transport = transport

    @classmethod
    def from_environment(cls):
        return cls(
            httpx.Client(
                base_url=os.environ.get(
                    "NOTES_API_URL",
                    "http://127.0.0.1:8000",
                )
            )
        )

    def list_notes(self):
        return self.transport.get("/notes/").json()
""",
        "packages/notes_client/tests/test_client.py": """\
def test_list_notes(client):
    assert isinstance(client.list_notes(), list)
""",
        "packages/notes_client/tests/conftest.py": """\
import pytest
from notes_client.client import NotesClient


class Transport:
    def get(self, path, **kwargs):
        class Response:
            def json(self):
                return []
        return Response()


@pytest.fixture
def client():
    return NotesClient(Transport())
""",
        "apps/notes_cli/README.md": """\
# notes CLI

Run `notes list` to print every note through `notes_client`.
""",
        "apps/notes_cli/pyproject.toml": """\
[project]
name = "notes-cli"
version = "0.1.0"

[project.scripts]
notes = "notes_cli.cli:main"
""",
        "apps/notes_cli/cli.py": """\
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
""",
        "apps/notes_cli/tests/test_cli.py": """\
def test_list_command(capsys, client):
    list_command(client)
    assert capsys.readouterr().out
""",
        "apps/notes_cli/tests/conftest.py": """\
import pytest


class Client:
    def list_notes(self):
        return [{"id": 1, "title": "First"}]


@pytest.fixture
def client():
    return Client()
""",
    },
    "tg06-eleventy-author-migration": {
        **ELEVENTY_BASE,
        "content/posts/first.md": """\
---
title: First post
author: "Ada Example"
---
First.
""",
        "content/posts/second.md": """\
---
title: Second post
author: "Grace Example"
---
Second.
""",
        "_includes/layouts/post.njk": """\
<h1>{{ title }}</h1>
<p class="author">{{ author }}</p>
{{ content | safe }}
""",
        "content/feed.xml.njk": """\
---
permalink: /feed/feed.xml
layout: false
---
<feed>{% for post in collections.posts %}<entry><author>{{ post.data.author }}</author></entry>{% endfor %}</feed>
""",
        "scripts/new-post.js": """\
export function frontMatter(title, author) {
  return `---\\ntitle: ${title}\\nauthor: "${author}"\\n---\\n`;
}
""",
        "tests/author-output.test.js": """\
// Generated-output coverage verifies the legacy author string on pages/feed.
""",
    },
}