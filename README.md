# Phoenix

An open-source social media analysis platform for peacebuilders.

Phoenix is a powerful, multi-tier platform that enables peacebuilders and analysts to monitor,
analyze, and visualize social media data for conflict prevention and peacebuilding efforts.

## Where to start

Phoenix offers several components tailored to different users' needs, from peacebuilders to
experienced software engineers. You can choose from three primary levels of interaction:

## Managed Platform

Since January 2025, Build Up offers a managed platform that is free to use for peacebuilders. Learn
more at [Build Up Phoenix](https://howtobuildup.org/phoenix/).

### 1. Platform

The **Phoenix Platform** is a full-stack web application providing a user-friendly interface to manage
configurations, collect and process social media data, and visualize results. It is designed for
peacebuilders and analysts (not deep in the code) who need a comprehensive toolset to monitor and
analyze social media activity.

* **Best for**: A team of engineers that want to offer phoenix to multi users who need a
  full-featured, out-of-the-box solution.
* **Setup complexity**: Highest, but includes the richest features.
* **Gotchas**: Be sure to review
  [`docs/administrating_phoenix.md`](docs/administrating_phoenix.md) if you're planning to set up
  a platform.
* **Getting Started**: Start with the [Platform Local Quick Start](#platform-quick-start) section
  below,  then check out [`charts/main/README.md`](charts/main/README.md) for more information on
  deploying the platform using the Helm chart.

### 2. PhiPhi API

The **PhiPhi API** is a RESTful API designed for developers who want to manage configurations,
collect data, and integrate Phoenix with other systems (such as visualization platforms). The API
includes auto-generated documentation via a Swagger web interface that allows developers to explore
and use the API endpoints.

* **Best for**: Developers wanting to manage multiple projects or integrate Phoenix with other
  systems.
* **Setup complexity**: Medium. Requires cloud deployment for practical use.
* **Documentation**: See the [PhiPhi Readme](python/projects/phiphi/README.md) for more
  information.

### 3. PhiPhi Pipeline Jobs

The **PhiPhi Pipeline Jobs** are a set of Python-based Prefect flows for developers who prefer to
collect and process social media data locally. This component is ideal for developers working on a
limited number of projects and is the easiest to set up.

* **Best for**: Developers who want get going quick, can manage their own data collection and
  processing locally.
* **Setup complexity**: Lowest, but requires developers organise configuration.
* **Documentation**: See the [PhiPhi Pipeline Jobs
  Readme](python/projects/phiphi/docs/getting_started_with_pipeline_jobs.md) for setup
  instructions.

## Platform Local Quick start

### Requirements

- [asdf](https://asdf-vm.com/guide/getting-started.html)
- [microk8s](https://microk8s.io/docs/install-alternatives)

```bash
make setup_asdf
source setup_microk8s.sh
make up
```

Visit in your browser:
- [http://console.phoenix.local](http://console.phoenix.local)
- [http://api.phoenix.local/docs](http://api.phoenix.local/docs)

More detailed documentation at [docs/development_getting_started.md](docs/development_getting_started.md).

## Organizations

<a href="https://howtobuildup.org">
    <img
      src="https://howtobuildup.org/wp-content/uploads/2021/04/build-up-logo.png"
      height="100"
      alt="build-up-logo"
    >
</a>
<a href="http://datavaluepeople.com">
    <img
      src="https://howtobuildup.org/wp-content/uploads/2022/03/dvp.png"
      height="100"
      alt="datavaluepeople_logo"
    >
</a>

## License

[GNU AGPLv3](/COPYING)

## v1

If you are looking for the old version it is [here](https://gitlab.com/howtobuildup/phoenix_v1). 
