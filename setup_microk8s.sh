echo "Setting up cluster"
microk8s enable ingress
microk8s enable dns
microk8s enable registry
microk8s enable hostpath-storage
microk8s config > ~/.kube/microk8s-config
source ./use_mircok8s.sh

echo "#######################################################"
echo "You need to add the following line to your /etc/hosts file"
echo "    127.0.0.1       dashboard.main.phoenix.local"
echo "    127.0.0.1       oauth.phoenix.local"
echo "    127.0.0.1       api.phoenix.local"
echo "    127.0.0.1       console.phoenix.local"
echo ""
echo "#######################################################"
