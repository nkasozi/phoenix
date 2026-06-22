setup_asdf:
	echo "Setting up asdf"
	asdf plugin list | grep -q helm || asdf plugin add helm
	asdf plugin list | grep -q tilt || asdf plugin add tilt
	asdf plugin list | grep -q nodejs || asdf plugin add nodejs
	asdf plugin list | grep -q kubectl || asdf plugin add kubectl https://github.com/asdf-community/asdf-kubectl.git
	asdf install
	asdf reshim

# Variables to define paths and contexts
LOCAL_DIR := clusters/local
LOCAL_WITH_AUTH_DIR := clusters/local_with_auth
DEV_DIR := clusters/dev
EXAMPLE_SECRETS := charts/main/example_secrets.yaml
TILT := tilt

# Helper command to start tilt
define tilt_up
	@echo "Checking if $(1)/secrets.yaml exists"
	if [ -f $(1)/secrets.yaml ]; then \
		$(TILT) up -f $(2); \
	else \
		echo "File $(1)/secrets.yaml does not exist."; \
		echo "Copying the example file"; \
		cp $(EXAMPLE_SECRETS) $(1)/secrets.yaml; \
		echo "Please fill in the $(1)/secrets.yaml file and run 'make $(3)' again"; \
	fi
endef

# Helper command to clean up resources
define tilt_clean
	$(TILT) down -f $(1);
	@echo "Deleting all PVCs in the $(2) namespace of the $(3) cluster."
	kubectl delete pvc --all -n $(2) --context $(3)
endef

up:
	$(call tilt_up,$(LOCAL_DIR),Tiltfile,up)

clean:
	$(call tilt_clean,Tiltfile,default,microk8s)
	@echo "Cleaning up non-latest images from local registry..."
	@./cleanup_registry.sh

# Define specific targets using the helper commands
local_with_auth_up:
	$(call tilt_up,$(LOCAL_WITH_AUTH_DIR),Tiltfile.local_with_auth,up)

local_with_auth_clean:
	$(call tilt_clean,Tiltfile.local_with_auth,default,microk8s)

dev_up:
	$(call tilt_up,$(DEV_DIR),Tiltfile.dev,dev_up)

dev_clean:
	$(call tilt_clean,Tiltfile.dev,$(DEV_NAMESPACE),$(KUBE_DEV_CONTEXT))
