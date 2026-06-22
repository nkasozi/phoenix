# Phoenix Python monorepo

## Monorepo overview

This monorepo serves as a unified codebase, that contains all Python-code for Phoenix, split into
separate projects (or "applications"), and libraries, which are first party libraries that projects
can leverage.

This [article](https://medium.com/opendoor-labs/our-python-monorepo-d34028f2b6fa) is recommended
reading. This monorepo follows many of that patterns and implementation as laid out in that
article, for similar reasons as give.

### Structure

There are three main distinct areas of the repo:
- *The root directory*: this contains development toolings, tooling config, and generally all the
  things that are to do with to the development workflow that applies to all projects and
  libraries.
- *`projects` directory*: this contains a directory per project/application.
- *`libs` directory*: this contains a directory per library.

Note: `tests` live inside the `project` package, i.e. at `proejcts/$(project)/$(project)/tests`.
This greatly simplifies `mypy` usage (due to `mypy`s package discovery etc.) in the monorepo.

## Development

Use pyenv for python installation management.

### Setting up a development environment

1. **Create a virtual env for the project or library:** Use command `make create_venv path=...`,
   where `...` is the path to the project or library directory.
2. **Activate the virtual env:** Run the command in the message output by the previous step,
   `source ...`.
3. **Install the project or library as a package along with its dependencies:** Use the command
   `make install path=...`.
4. **Verify the setup:** Start a Python interpreter and check you import the project/library. Run
   `make all path=...` and check all passes.

### Project dependency management

To modify a project's dependencies, follow these steps:
1. Edit `projects/$(projects)/requirements.in`.
2. Run `make compile_requirements path=...`.
3. Review and commit changes.
4. Reinstall deps by running `make install path=...`.

To upgrade a project's dependencies to the latest versions available, use `make
upgrade_requirements path=...` in the above flow.

### Library dependency management

Note that libraries shouldn't have a compiled `requirements.txt` file. Packages (generally, not
just in this monorepo) shouldn't specify certain versions of its dependencies - this enables the
users of the libs to specify versions they want.

Libraries specify their (loose) requirements in their `libs/$(lib)/pyproject.toml` file.

### Change active development environment

1. Deactivate the current virtual env by running `deactivate`.
2. Active the desired project/lib virtual env with `source
   projects/$(project)/.$(project)_venv/bin/activate`, likewise for libs.

## Adding new Projects and Libs

For now, the process is to make a copy of `example_...` dir, and change the relevant bits.

