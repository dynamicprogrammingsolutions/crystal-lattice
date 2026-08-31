from pathlib import Path

from dotenv import load_dotenv


def pytest_configure() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env", override=False)
