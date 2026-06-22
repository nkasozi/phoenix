# Locally debugging flows which include a `prefect.run_deployment(...)` call

In most cases, integration tests are sufficient for debugging flows. However, there are scenarios
where debugging a flow that calls other flows using `run_deployment` requires additional steps.
Running such flows locally can save time by avoiding repeated image rebuilds when testing with a
local cluster.

This guide explains how to set up a local debugging environment where flows using `run_deployment`
call other flows via a local Prefect server.

---

## Overview

The approach involves:
1. Running a local Prefect server on your local cluster.
2. Configuring your PhiPhi Docker environment to use this local Prefect server.
3. Running and debugging the flow locally. Any flows triggered by `run_deployment` will use the
   local Prefect server.

---

## Setup Steps

### 1. Start the Local Cluster
- Follow the instructions in the root `README.md` to start the local cluster.

### 2. Get the Prefect Server IP
- Open a new terminal and configure `kubectl` for the local cluster by running:
  ```bash
  source use_microk8s.sh
  ```
- Retrieve the Prefect server's IP address using:
  ```bash
  kubectl get service/prefect-server
  ```
  The IP is under the column `CLUSTER-IP`.

### 3. Set PREFECT_API_URL in PhiPhi Docker
- In your Docker environment, set the `PREFECT_API_URL` to point to the local Prefect server:
  ```bash
  PREFECT_API_URL=http://<IP>:4200/api
  ```
  Replace `<IP>` with the IP address from step 3.
- Instructions for setting environment variables in the Docker container are provided in a later
  section but it can be done in other ways if you prefer.

### 4. Start and Access the PhiPhi Docker Container
- Start the Docker container with:
  ```bash
  make up
  ```
- Open a shell in the container:
  ```bash
  make bash_in_api
  ```

### 5. Configure Environment Variables in the Container (if not done in step 3)
- Inside the container, set the following environment variables:
  ```bash
  export PREFECT_API_URL=http://<IP>:4200/api
  export PREFECT_API_KEY=""
  ```

## Running the Flow
1. Create a Script: Write or modify an existing script to run your flow. Refer to the examples
   section below for guidance.
2. Add Breakpoints: Insert `import pdb; pdb.set_trace()` in your script to enable interactive
   debugging.
3. Note on run_deployment:
  * Flows triggered via `run_deployment` will run on the Prefect worker in the local cluster.
  * Be aware that `flow_runner_flow` will interact with the platform DB in your Docker Compose
    environment, not the local cluster.

## Examples
Refer to the following example for implementation details:
[run_test_flow_runner_flow.py](python/projects/phiphi/phiphi/api/projects/job_runs/run_test_flow_runner_flow.py)
