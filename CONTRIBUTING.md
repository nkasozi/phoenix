# CONTRIBUTING.md

## Welcome

Thank you for considering contributing to the `phoenix` project! We welcome contributions from
everyone, and are grateful for any help, big or small. This document is a guide to help you
understand how you can contribute.

## How to Contribute

Contributions to `phoenix` can come in various forms. Here are some ways you can help:

* **Bug Reports**: If you find a bug, please open an issue in our GitLab repository. Include a
  detailed description of the bug, steps to reproduce it, and, if possible, a suggestion for how it
  could be fixed.
* **Feature Requests**: Have an idea for a new feature or an improvement to an existing one? Submit
  an issue, describing your idea and how it would benefit the project.
* **Code Contributions**: Ready to start coding? Great! Look through our issues for tasks to
  tackle, or suggest your own ideas as a new issue. Once you're ready, submit a Merge Request (MR)
  with your changes.
* **Other ways**: See [phoenix landing
  page](https://howtobuildup.org/phoenix/)

## Principles

These principles give guidelines and direction for collaborating and developing the repository.

### General Principles

* We prioritise the understandability and usability of everything do
* We support and respect one another: we can be tough on ideas but are always gentle on people
* We are not violent or derogatory
* We resolve conflict through peaceful and pragmatic ways
* We tend towards combining already existing tools and ideas rather than coming up with our own
* We work asynchronous and are aware of the requirements for this, [more info in a blog from
  gitlab](https://about.gitlab.com/company/culture/all-remote/asynchronous/#how-does-asynchronous-communication-work)
* We aim to be concise and considerate in our communication
* There is no right and wrong, there are advantages and disadvantages

### Coding Principles

* We prioritise the understandability and usability of everything do
* We aim to write documentation first, have that reviewed and then implement the feature
* We try to make small understandable changes: with commits that are atomic and MRs (PRs) that are
  like short stories for the reviewer, see below for resources
* We attempt to make software tools that follow the Unix philosophy of “Doing one thing well”,
  [more info here](http://www.catb.org/~esr/writings/taoup/html/ch01s06.htm)

#### Further reading and resources

* [On MRs (PRs)](https://wiki.crdb.io/wiki/spaces/CRDB/pages/1411744698/Organizing+PRs+and+Commits)

## Getting Started

1. Fork the repository on GitLab. This creates your own copy of the project, where you can make
changes without affecting the original.
2. Clone your fork to your local machine, so you can start working on the changes.
3. Create a new branch for your changes. This keeps your modifications organized and separate from
the main branch.
4. Make your changes. Be sure to follow the coding standards and guidelines of the project.
5. Test your changes. Ensure that your code does not break any existing functionality and meets the
project's quality standards.
6. Submit a Merge Request. Go to the original Phoenix repository on GitLab and click on "Merge
Requests". Click "New Merge Request", and select your fork and branch as the source. Fill in the
details, explaining your changes and why they should be included. Generally MRs should be made on
to `dev` and not `main`.

## Release Process

The release process is managed by the maintainers of the project. If you have a feature or bug fix
that you would like to see included in the next release, please submit a Merge Request with `dev` as
the target branch. The maintainers will review your changes and decide whether to include them in
the next release.

To make a release, the maintainers will follow these steps:
- In this repo:
  - Merge all approved changes in to `dev`
  - Pull `dev` locally: `git checkout dev`, `git pull`
  - Update the version number in:
    - [./charts/main/Chart.yaml](./charts/main/Chart.yaml), `version` and `appVersion`
  - Commit these changes to `dev` with a commit message like "Bump version 2.6.0"
  - Add a tag to the commit with the version number, `git tag -a 2.6.0`, with a message that
    follows the convention of the other tags, e.g. `Release 2.6.0` then a description of what has
    changed. Currently we don't automatically generate this but it is good to give an indication of
    what is being released.
  - Push the tag to `dev` `git push --follow-tags`
  - This will start the CI/CD pipeline for the tag and create a release, [releases page](https://gitlab.com/howtobuildup/phoenix/-/releases)
  - Create a MR from `dev` to `main` (this will contain changes for release and the commit with the
    version change). Be aware there will be two pipelines, one for the MR, and one for the tag -
    the tag pipeline creates the "release" (building and pushing the docker images etc).
  - TEMPORARY: Due to the limit on the size of the gitlab runner the CI is not able to build the
    nvidia image needed for the hugging face classifier. Therefore you need to build and push the
    image with the following commands (SET VERSION and TOKEN needs to be a [GitLab personal access
    token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)):
    ```bash
    TOKEN=<SET ME> # needs to have write_registry and read_registry
    USERNAME=<SET ME> # your gitlab username
    VERSION=<SET ME> # the version you are releasing, e.g. 2.6.0
    echo "$TOKEN" | docker login registry.gitlab.com -u $USERNAME --password-stdin
    docker build -f Dockerfile.nvidia --build-arg PROJECT=hugging_face_classifier -t hugging_face_classifier .
    docker tag hugging_face_classifier:latest registry.gitlab.com/howtobuildup/phoenix/python/hugging_face_classifier:nvidia-$VERSION
    docker push registry.gitlab.com/howtobuildup/phoenix/python/hugging_face_classifier:nvidia-$VERSION
    ```
  - Once the release pipeline has completed (from the tag push), and building and pushing the
    `hugging_face_classifier` image has completed, all the artefacts and images will be available,
    and you can merge the MR into `main`, then move on to deploying the new version to the dev and
    prod infrastructure.
- Phoenix also has a managed instance, run by Build Up. To release the latest version to this
  managed service go to the `phoenix-infra` repo and:
  - Create an MR repo which changes the variables for the chart version (named
    `helm_phoenix_main.chart_version`) in the files `dev.tfvars` and `prod.tfvars` to the new
    version.
  - Once the pipeline for the MR in `phoenix-infra` has passed, check the plans, and if correct,
    merge the MR.
  - Once the MR is merged is will trigger a merge pipeline - once this has completed, you need to
    manually trigger the "apply" step at the end of the pipeline **just for `dev`** initially. This
    will deploy the new version to the dev environment.
  - (It is also possible to apply tofu environments to the `dev` environment from your local
    machine to future test if needed.)
  - Once everything looks good on dev, manually trigger the "apply" step at the end of that same
    pipeline this time for `prod`.
- If you changes included changes to the Project databases (these are the, one per user project,
  GCP BigQuery databases, that hold the scraped data etc), then you also need to run the following:
    - Get into the UI for the Prefect server running in `prod` (see the Phoenix - developer manual`
      doc).
    - Find the Deployment `apply_migrations_for_projects`, and run it with: `job_run_id=-1`,
      `start=0`, `end=500`. This will apply the latest migrations to all projects.
    - Check all the subflows run successfully.
- (The front-end is automatically deployed with `Aws Amplify` (from `main` and the backend is
  deployed with `Helm` to the `prod` environment.)

### Helpful

* [Development Getting Started](/docs/development_getting_started.md)

## Communication

Use GitLab issues to ensure that everyone can participate and the conversation is recorded. Or see
[phoenix landing page](https://howtobuildup.org/phoenix/)

## Thank You

Every contribution is valuable to the project. Thank you for your hard work and dedication.
