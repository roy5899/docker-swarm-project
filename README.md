# High-Availability API Infrastructure & Centralized Observability Stack

## Project Overview
This project demonstrates a production-grade, multi-tier architecture deployed on AWS using **Docker Swarm**. It hosts multiple isolated backend services (NestJS and FastAPI) behind an NGINX reverse proxy, fully integrated with an enterprise observability stack for real-time metrics and centralized logging. 

The infrastructure is designed with Site Reliability Engineering (SRE) principles in mind: zero-downtime deployments, self-healing container orchestration, persistent storage management, and automated CI/CD pipelines.

## Tech Stack
* **Cloud Infrastructure:** AWS EC2 (t3.medium), AWS EBS (Persistent Storage)
* **Orchestration:** Docker Swarm
* **Routing / Proxy:** NGINX
* **Backend APIs:** Node.js (NestJS), Python (FastAPI)
* **Metrics & Monitoring:** Prometheus, cAdvisor, Grafana
* **Centralized Logging:** Grafana Loki, Promtail
* **CI/CD:** GitHub Actions

---

## Architectural Approach & Design Decisions

### 1. Storage & State Management
To prevent root volume exhaustion (a common cause of node failure), the Docker daemon's `data-root` (`/var/lib/docker` and `containerd`) was migrated via symlinks to a dedicated **30GB AWS EBS volume**. This ensures that image layers, container logs, and database volumes (like Grafana's SQLite DB) do not compete with the host OS for disk space.

### 2. Network Isolation
Security and multi-tenant isolation are enforced using **Docker Swarm Overlay Networks**. 
* `client_a_net` & `client_b_net`: Strictly isolates the application backends.
* `proxy_net`: A shared network allowing the NGINX ingress to route traffic to the respective isolated applications.

### 3. Lightweight Observability
Instead of deploying the resource-heavy ELK stack (Elasticsearch, Logstash, Kibana), **Grafana Loki and Promtail** were chosen for centralized logging. Loki indexes only metadata labels rather than full log text, drastically reducing RAM and CPU consumption while natively integrating with the existing Grafana dashboard for a single pane of glass.

---

##Scaling, High Availability & Orchestration

### Manual Scaling
Scaling up services to handle increased load requires a single declarative command. Swarm's Routing Mesh automatically adds the new containers to the load balancer pool.
`docker service scale my_stack_client-a-node-app=5`

### Zero-Downtime Rolling Updates
The stack is configured for seamless updates without dropping incoming client requests. The `docker-stack.yml` utilizes the following deployment strategy:
```yaml
deploy:
  update_config:
    parallelism: 1
    delay: 10s
    failure_action: rollback
```

## **How it works:** 
When a new image is deployed via GitHub Actions, Swarm updates one container at a time (parallelism: 1), waits 10 seconds to ensure stability (delay: 10s), and routes traffic to the new container before killing the old one. If the new container fails its healthcheck, Swarm automatically triggers a rollback to the previous stable state.
## **Service Discovery & Load Balancing**
Swarm features built-in internal DNS. Containers do not need to know IP addresses; they communicate purely via service names.

Example: Promtail forwards logs to Loki simply by calling http://loki:3100.
Additionally, Swarm's VIP (Virtual IP) Routing Mesh acts as an internal load balancer, evenly distributing incoming requests across all healthy replicas of a service.

## **Multi-Tenant Scaling Strategy (Whiteboard Scenario)**
**Objective**: Scale the architecture to onboard 20 new enterprise clients monthly efficiently.

If tasked with scaling this to a massive multi-tenant environment, I would implement the following architecture:

**Dynamic Ingress:** Replace static NGINX with Traefik. Traefik natively reads Swarm labels, allowing new client APIs to be routed dynamically without manually reloading reverse proxy configurations.

**Infrastructure Auto-Scaling:** Wrap Swarm Worker nodes in an AWS Auto Scaling Group (ASG). As overall cluster CPU utilization spikes, the ASG provisions new EC2 Spot Instances. A cloud-init script automatically runs docker swarm join on boot, allowing the cluster to expand horizontally.

**Strict Resource Constraints:** Enforce deploy.resources.limits (CPU and Memory) on every client's stack to prevent "noisy neighbor" scenarios where one heavy client crashes the shared node.

**Secrets Management:** Deprecate .env files in favor of Docker Swarm Secrets, ensuring sensitive database credentials for Client A cannot be accessed by Client B's containers.

## **CI/CD Pipeline**
Continuous Deployment is handled via **GitHub Actions**. Upon merging to the main branch, the workflow:
* Establishes a secure **SSH connection** to the AWS Swarm Manager.
* Pulls the latest infrastructure code.
* Executes ```docker stack deploy -c docker-stack.yml my_stack_service``` to trigger the rolling update.
