# 🚀 DevOps Guide: Insurance Fraud Detection

Welcome to your DevOps journey! This guide will walk you through setting up and running your project using **Docker** and **Kubernetes**. 

## 🏗️ What We Are Building
We are turning your local Python app into a "cloud-ready" system. Instead of running scripts manually, we use:
- **Docker**: To package your app so it runs exactly the same on any computer.
- **Kubernetes (K8s)**: To manage these packages, ensuring they stay running and can scale.
- **GitHub Actions**: To automatically test your code every time you save it.

---

## 🛠️ Prerequisites
Before starting, make sure you have these tools installed:
1. **Docker Desktop**: [Download here](https://www.docker.com/products/docker-desktop/)
2. **Kubectl**: The command-line tool for Kubernetes. (Usually installed with Docker Desktop).
3. **Minikube**: A way to run a small Kubernetes cluster on your laptop. [Install guide](https://minikube.sigs.k8s.io/docs/start/)

---

## 🏁 Step 1: Building your Containers
Containers are like "boxes" for your code. Let's build the API and the Frontend boxes.

Open your terminal in the `IR-Project` folder and run:

```bash
# Build the backend API image
docker build -t fraud-api:latest -f Dockerfile.api .

# Build the frontend Streamlit image
docker build -t fraud-streamlit:latest -f Dockerfile.streamlit .
```

---

## 🎡 Step 2: Starting Kubernetes
We'll use **Minikube** to create a mini "cloud" on your machine.

```bash
# Start the cluster
minikube start

# Tell your terminal to use the Docker daemon inside Minikube
# (This allows Kubernetes to see the images you just built)
minikube docker-env | Invoke-Expression  # For PowerShell
# OR
eval $(minikube -p minikube docker-env) # For Bash/Zsh
```

---

## 🚀 Step 3: Deploying to Kubernetes
Now we tell Kubernetes to run our boxes. We use the files in the `k8s/` folder.

```bash
# 1. Deploy the API
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml

# 2. Deploy the Streamlit Frontend
kubectl apply -f k8s/streamlit-deployment.yaml
kubectl apply -f k8s/streamlit-service.yaml
```

Check if they are running:
```bash
kubectl get pods
```
*Wait until the status says `Running`.*

---

## 🌐 Step 4: Accessing the App
By default, Kubernetes services are "internal". We need to open a door to see the frontend.

```bash
# This will give you a link to open in your browser
minikube service streamlit-service
```

---

## 🤖 Step 5: Automation (CI/CD)
I've already created a file at `.github/workflows/ci.yml`. 
Every time you `git push` your code to GitHub, it will:
1. **Test**: Run your sanity checks.
2. **Build**: Ensure the Docker images still work.

---

## 💡 Pro Tips for Beginners
- **Logs**: If something crashes, run `kubectl logs <pod-name>` to see why.
- **Restart**: If you change your code, you need to rebuild the Docker image and run `kubectl rollout restart deployment <name>`.
- **Cleanup**: Run `minikube stop` when you're done to save battery/RAM.
