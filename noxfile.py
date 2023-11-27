import os
import shutil

import nox

nox.options.reuse_existing_virtualenvs = True

PYTHON_VERSIONS = ['pypy3', '3.8', '3.9', '3.10', '3.11', '3.12']
CI_ENVIRONMENT = 'GITHUB_ACTIONS' in os.environ


@nox.session(python=PYTHON_VERSIONS[-1])
def lint(session):
    """Performs pep8 and security checks."""
    source_code = 'ws'
    session.run('poetry', 'install', '--only', 'lint')
    session.run('ruff', 'check', source_code)
    session.run('bandit', '-r', source_code)


@nox.session(python=PYTHON_VERSIONS[-1])
def safety(session):
    """Checks vulnerabilities of the installed packages."""
    session.run('poetry', 'install', '--only', 'security')
    session.run('safety', 'check')


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Runs the test suite."""
    session.run('poetry', 'install', '--with', 'test')
    session.run('pytest')


@nox.session(python=PYTHON_VERSIONS[-1])
def docs(session):
    """Builds the documentation."""
    session.run('poetry', 'install', '--only', 'docs')
    session.run('mkdocs', 'build', '--clean')


@nox.session(python=False)
def deploy(session):
    """
    Deploys on pypi.
    """
    if 'POETRY_PYPI_TOKEN_PYPI' not in os.environ:
        session.error('you must specify your pypi token api to deploy your package')

    session.run('poetry', 'publish', '--build')


@nox.session(python=False)
def clean(*_):
    """Since nox take a bit of memory, this command helps to clean nox environment."""
    shutil.rmtree('.nox', ignore_errors=True)
