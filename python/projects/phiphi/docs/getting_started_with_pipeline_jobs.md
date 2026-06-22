# Getting Started with Pipeline Jobs

**PhiPhi Pipeline Jobs** are a set of Python-based Prefect flows designed for developers who need to
collect and process social media data independently. These flows allow for flexible, customizable
data pipelines that can be executed locally, giving developers full control over how they collect
and process data.

## Who Should Use PhiPhi Pipeline Jobs?

* **Target Audience**: Developers looking to manage their own social media data collection and
  processing pipelines.
* **Use Cases**: Ideal for working on a limited number of projects, where local data processing and
  custom pipelines are preferred over larger, cloud-hosted systems.

If you are comfortable with Python and want more control over your data collection and processing
workflows, PhiPhi Pipeline Jobs are a great choice.

## Features

* **Customizable**: Write your own data processing logic using Python and Prefect.
* **Local Execution**: Run and manage flows on your local machine for smaller projects. With data
  persisted in to google cloud's big query.
* **Extensible**: Integrate with other tools and systems as needed.

## Documentation Status

We are still working on comprehensive documentation for PhiPhi Pipeline Jobs. In the meantime,
here’s how you can get started:

* **Clone the repository** and explore the existing Prefect flows in the pipeline_jobs directory.
* **Set up the development environment** by following the instructions in  
  [`python/projects/phiphi/README.md`](python/projects/phiphi/README.md).
* **Run the flows**: by following the section [Running Commands in the Development
  Environment](python/projects/phiphi/README.md###running-comands-in-the-development-environment)
* **Create scripts** — you can also write and execute your own scripts within the container to
  streamline development.
* **Reach out** to us if you have any questions or need assistance. We’re here to help!

## Contribute

If you're interested in contributing to the project by improving the documentation or adding new
features, we would love to collaborate with you. Whether you're a seasoned developer or just
getting started, any contribution is welcome!

Feel free to open issues or pull requests with any improvements you make, and let's build something
impactful together.
