FROM nginx:1.25.4

# Remove the default nginx.conf
RUN rm /etc/nginx/conf.d/default.conf

# So we can use different configurations at build time
ARG NGINX_CONF=local_phoenix_superset.conf

# Copy the custom nginx.conf into the container
COPY $NGINX_CONF /etc/nginx/conf.d
