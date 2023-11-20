import shutil
from pathlib import Path
from typing import Mapping

import nox

PDOC_FAVICON = "https://github.com/object-Object/hexdoc/raw/main/media/hexdoc.png"
PDOC_LOGO_LINK = "https://pypi.org/project/hexdoc/"
PDOC_LOGO = "https://github.com/object-Object/hexdoc/raw/main/media/hexdoc.svg"
PDOC_EDIT_URL = "https://github.com/object-Object/hexdoc/blob/main/src/hexdoc/"

nox.options.reuse_existing_virtualenvs = True

nox.options.sessions = ["tests"]


# sessions


@nox.session
def tests(session: nox.Session):
    session.run("pip", "uninstall", "hexdoc-mod", "-y")
    session.install("-e", ".[test]", "-e", "./test/_submodules/HexMod")

    # this apparently CANNOT run from pre-commit in GitHub Actions (venv issues)
    session.run("pyright", "src", "--warnings")

    # test cookiecutter last so the extra package install doesn't interfere
    session.run("pytest", "--nox", *session.posargs)


@nox.session
def pdoc(session: nox.Session):
    session.install(".[pdoc]")

    version = run_silent(session, "hatch", "version")
    commit = run_silent_external(session, "git", "rev-parse", "--short", "HEAD")

    session.run(
        "pdoc",
        "hexdoc",
        "--favicon",
        PDOC_FAVICON,
        "--logo-link",
        PDOC_LOGO_LINK,
        "--logo",
        PDOC_LOGO,
        "--edit-url",
        f"hexdoc={PDOC_EDIT_URL}",
        "--footer-text",
        f"Version: {version} ({commit})",
        *session.posargs,
    )


@nox.session
def hexdoc(session: nox.Session):
    session.install(".")
    session.run("hexdoc", *session.posargs)


@nox.session
def mock_ci(session: nox.Session):
    session.install(".", "hatch")
    session.install("./test/_submodules/HexMod", "--no-deps")
    session.install("../hexdoc-minecraft", "--no-deps")  # TODO: remove

    github_path = Path("out/github")

    shutil.rmtree("_site", ignore_errors=True)
    shutil.rmtree(github_path, ignore_errors=True)

    github_path.mkdir(parents=True)

    with session.cd("test/_submodules/HexMod"):
        github_sha = run_silent_external(session, "git", "rev-parse", "HEAD")

    session.env.update(
        GITHUB_ENV=str(github_path / "env.txt"),
        GITHUB_OUTPUT=str(github_path / "output.txt"),
        GITHUB_REF_NAME="main",
        GITHUB_REPOSITORY="object-Object/HexMod",
        GITHUB_SHA=github_sha,
        GITHUB_TOKEN=run_silent_external(session, "gh", "auth", "token"),
        HEXDOC_PROPS="test/_submodules/HexMod/doc/hexdoc.toml",
        HEXDOC_RELEASE="true",
    )
    if "-v" in session.posargs or "--verbose" in session.posargs:
        session.env.update(RUNNER_DEBUG="1")

    session.run("hexdoc", "ci", "export")

    session.run("hexdoc", "ci", "render", "en_us")
    session.run("hexdoc", "ci", "render", "zh_cn")

    shutil.move("_site", "_site_tmp")
    shutil.move("_site_tmp", "_site/src/docs")

    session.run("hexdoc", "ci", "merge")


# utils


def run_silent_external(
    session: nox.Session,
    *args: str,
    env: Mapping[str, str] | None = None,
):
    return run_silent(session, *args, env=env, external=True)


def run_silent(
    session: nox.Session,
    *args: str,
    env: Mapping[str, str] | None = None,
    external: bool = False,
):
    output: str | None = session.run(
        *args,
        env=env,
        silent=True,
        external=external,
    )
    assert output
    return output.strip()
