# Superset version must be the same as in `requirements.in`
FROM apache/superset:5.0.0

# Install the driver requirements.
# Using an .in file rather than a .txt file as
# this is what is documented in the docker image:
# https://hub.docker.com/r/apache/superset
COPY ./docker.requirements.in /app/phoenix_superset/docker.requirements.in
USER root

# Activate the virtual environment and install packages
RUN . /app/.venv/bin/activate && \
    uv pip install --no-cache-dir -r /app/phoenix_superset/docker.requirements.in

# Set environment variable for Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/playwright-browsers

# Install playwright packages
RUN . /app/.venv/bin/activate && \
    playwright install-deps \
    && PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/playwright-browsers playwright install chromium

# We are not using the default /app/pythonpath directory
# as in superset helm everything is overwritten there.
# Using /app/phoenix_superset/ as a pythonpath.
# Usage:
# `from phoenix_superset import custom_sso_manager`
# `CUSTOM_SSO_MANAGER = custom_sso_manager.PhoenixCustomSSOSecurityManager`
# in the config.py file or config override.
COPY ./phoenix_superset/ /app/phoenix_superset/phoenix_superset/
ENV PYTHONPATH=/app/phoenix_superset/:$PYTHONPATH

# Copy and phoenix_superset/config.py file
COPY ./config.py /app/phoenix_superset/config.py

# Copy the phoenix_superset scripts
COPY ./phoenix_superset_scripts/ /app/phoenix_superset/scripts/

USER superset

## Assets
# Copy the assets to the /app/assets directory
COPY ./assets/images/* /app/superset/static/assets/images/
COPY ./templates/* /app/superset/templates/
