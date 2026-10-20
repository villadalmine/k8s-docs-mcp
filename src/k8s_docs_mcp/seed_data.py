from typing import List, Dict, Any
from k8s_docs_mcp.models import K8sDocSection, K8sManifest


def get_seed_sections() -> List[K8sDocSection]:
    """Returns canonical seed documentation sections for core Kubernetes concepts."""
    return [
        K8sDocSection(
            title="Network Policies",
            url="https://kubernetes.io/docs/concepts/services-networking/network-policies/",
            source_file="content/en/docs/concepts/services-networking/network-policies.md",
            section_name="NetworkPolicy Resource Definition",
            content="""Network policies are an application-centric construct that allow you to specify how a pod is allowed to communicate with various network 'entities' over the network.
Network policies apply to a connection with a pod on one or both ends, and are not relevant to other connections.
Entities that a Pod can communicate with are identified through a combination of:
1. Other pods that are allowed (pods cannot block access to themselves).
2. Namespaces that are allowed.
3. IP blocks (exceptions: traffic to and from the node where a Pod is running is always allowed).

By default, network policies are additive: if any policy or policies selecting a pod allow a connection, the connection is allowed.
If a pod is selected by one or more NetworkPolicies with policyTypes including Ingress, then ingress traffic to that pod is restricted to what is explicitly allowed.
""",
            tags=["networking", "security", "networkpolicy"],
        ),
        K8sDocSection(
            title="Validating Admission Webhooks",
            url="https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/",
            source_file="content/en/docs/reference/access-authn-authz/extensible-admission-controllers.md",
            section_name="ValidatingWebhookConfiguration",
            content="""Admission webhooks are HTTP callbacks that receive admission requests and do something with them.
You can define two types of admission webhooks: validating admission webhooks and mutating admission webhooks.
Mutating admission webhooks are invoked first, and can modify objects sent to the API server to enforce custom defaults.
After all object modifications are complete, and after incoming objects are validated by the API server, validating admission webhooks are invoked and can reject requests to enforce custom policies.
Admission webhooks are registered with the API server by creating ValidatingWebhookConfiguration or MutatingWebhookConfiguration objects.
""",
            tags=["admission", "security", "webhooks", "governance"],
        ),
        K8sDocSection(
            title="ValidatingAdmissionPolicy",
            url="https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/",
            source_file="content/en/docs/reference/access-authn-authz/validating-admission-policy.md",
            section_name="In-tree CEL Policy Enforcement",
            content="""Validating admission policies offer an in-process alternative to validating admission webhooks.
Validating admission policies use the Common Expression Language (CEL) to declare validation rules of admission requests.
CEL validation expressions evaluate quickly, without network roundtrips to out-of-tree webhook servers, improving cluster reliability and latency.
A ValidatingAdmissionPolicy describes the CEL validation rules and which resources are subject to validation, while a ValidatingAdmissionPolicyBinding binds the policy to specific namespaces or resources.
""",
            tags=["admission", "cel", "validatingadmissionpolicy", "governance"],
        ),
        K8sDocSection(
            title="Deployments",
            url="https://kubernetes.io/docs/concepts/workloads/controllers/deployment/",
            source_file="content/en/docs/concepts/workloads/controllers/deployment.md",
            section_name="Deployment Controller Overview",
            content="""A Deployment provides declarative updates for Pods and ReplicaSets.
You describe a desired state in a Deployment, and the Deployment Controller changes the actual state to the desired state at a controlled rate.
Use cases for Deployments:
- Create a Deployment to rollout a ReplicaSet.
- Declare the new state of the Pods by updating the PodTemplateSpec.
- Rollback to an earlier Deployment revision if current state is unstable.
- Scale up the Deployment to facilitate more load.
- Pause and resume Deployments to apply multiple fixes.
""",
            tags=["workloads", "deployment", "replicaset"],
        ),
        K8sDocSection(
            title="Role-Based Access Control (RBAC)",
            url="https://kubernetes.io/docs/reference/access-authn-authz/rbac/",
            source_file="content/en/docs/reference/access-authn-authz/rbac.md",
            section_name="RBAC Authorization API Objects",
            content="""Role-based access control (RBAC) is a method of regulating access to computer or network resources based on the roles of individual users within your organization.
RBAC authorization uses the rbac.authorization.k8s.io API group to drive authorization decisions, allowing you to dynamically configure policies through the Kubernetes API.
To enable RBAC, start the API server with the --authorization-mode=RBAC flag.
Core RBAC API objects:
- Role: Defines permissions within a specific namespace.
- ClusterRole: Defines permissions across the entire cluster or for non-namespaced resources.
- RoleBinding: Grants permissions defined in a Role or ClusterRole to a user or set of users within a namespace.
- ClusterRoleBinding: Grants permissions cluster-wide.
""",
            tags=["security", "rbac", "authorization"],
        ),
        K8sDocSection(
            title="Pods and Pod Lifecycle",
            url="https://kubernetes.io/docs/concepts/workloads/pods/",
            source_file="content/en/docs/concepts/workloads/pods.md",
            section_name="Pod Overview and Container Sharing",
            content="""Pods are the smallest deployable units of computing that you can create and manage in Kubernetes.
A Pod is a group of one or more containers, with shared storage and network resources, and a specification for how to run the containers.
Key Pod concepts:
1. Shared Networking: All containers in a Pod share the same network namespace, including IP address and network ports (they communicate via localhost).
2. Shared Storage: Pods can specify a set of shared storage Volumes accessible to all containers in the Pod.
3. Pod Lifecycle: A Pod transitions through phases: Pending -> Running -> Succeeded / Failed. If a container crashes, the kubelet restarts it according to restartPolicy (Always, OnFailure, Never).
4. Multi-container patterns: Sidecar (augmenting primary app, e.g. envoy or logging agent), Init Containers (run before app containers start), and Ambassador (proxying connections).
Pods are ephemeral by design and are typically managed by controllers like Deployments, StatefulSets, or DaemonSets rather than created directly in production.
""",
            tags=["workloads", "pods", "containers", "lifecycle"],
        ),
        K8sDocSection(
            title="Services and Networking",
            url="https://kubernetes.io/docs/concepts/services-networking/service/",
            source_file="content/en/docs/concepts/services-networking/service.md",
            section_name="Service Overview and Service Types",
            content="""An abstract way to expose an application running on a set of Pods as a network service.
With Kubernetes you don't need to modify your application to use an unfamiliar service discovery mechanism.
Kubernetes gives Pods their own IP addresses and a single DNS name for a set of Pods, and can load-balance across them.
Service Types:
- ClusterIP: Exposes the Service on an internal IP in the cluster (default). Accessible only within the cluster.
- NodePort: Exposes the Service on each Node's IP at a static port (30000-32767).
- LoadBalancer: Exposes the Service externally using an external cloud provider load balancer.
- ExternalName: Maps the Service to the contents of the externalName field (e.g. foo.bar.example.com).
""",
            tags=["networking", "services", "service-discovery"],
        ),
    ]


def get_seed_manifests() -> List[K8sManifest]:
    """Returns canonical verified YAML manifests for standard Kubernetes resources."""
    return [
        K8sManifest(
            kind="NetworkPolicy",
            api_version="networking.k8s.io/v1",
            name="test-network-policy",
            source_file="content/en/examples/service/networking/network-policy-default-deny-ingress.yaml",
            url="https://kubernetes.io/docs/concepts/services-networking/network-policies/#default-deny-all-ingress-traffic",
            content="""apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
""",
            description="Default deny all ingress traffic network policy.",
        ),
        K8sManifest(
            kind="NetworkPolicy",
            api_version="networking.k8s.io/v1",
            name="allow-web-ingress",
            source_file="content/en/examples/service/networking/network-policy-allow-ingress.yaml",
            url="https://kubernetes.io/docs/concepts/services-networking/network-policies/",
            content="""apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-traffic
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 8080
""",
            description="Allow incoming traffic on port 8080 from frontend pods.",
        ),
        K8sManifest(
            kind="ValidatingWebhookConfiguration",
            api_version="admissionregistration.k8s.io/v1",
            name="pod-policy.example.com",
            source_file="content/en/docs/reference/access-authn-authz/extensible-admission-controllers.md",
            url="https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/#webhook-configuration",
            content="""apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: "pod-policy.example.com"
webhooks:
- name: "pods.example.com"
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE", "UPDATE"]
    resources: ["pods"]
    scope: "Namespaced"
  clientConfig:
    service:
      namespace: "default"
      name: "admission-webhook-service"
      path: "/validate"
    caBundle: "Ci0tLS0tQk...tLS0K"
  admissionReviewVersions: ["v1"]
  sideEffects: None
  timeoutSeconds: 5
""",
            description="Canonical ValidatingWebhookConfiguration for Pod creation/update validation.",
        ),
        K8sManifest(
            kind="ValidatingAdmissionPolicy",
            api_version="admissionregistration.k8s.io/v1",
            name="demo-policy.example.com",
            source_file="content/en/docs/reference/access-authn-authz/validating-admission-policy.md",
            url="https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/",
            content="""apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: "demo-policy.example.com"
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups: ["apps"]
      apiVersions: ["v1"]
      operations: ["CREATE", "UPDATE"]
      resources: ["deployments"]
  validations:
    - expression: "object.spec.replicas <= 5"
      message: "Deployments cannot have more than 5 replicas."
""",
            description="In-tree CEL policy restricting Deployment replicas.",
        ),
        K8sManifest(
            kind="Deployment",
            api_version="apps/v1",
            name="nginx-deployment",
            source_file="content/en/examples/controllers/nginx-deployment.yaml",
            url="https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#creating-a-deployment",
            content="""apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.14.2
        ports:
        - containerPort: 80
""",
            description="Canonical NGINX Deployment manifest with 3 replicas.",
        ),
        K8sManifest(
            kind="Pod",
            api_version="v1",
            name="nginx-pod-single",
            source_file="content/en/examples/pods/simple-pod.yaml",
            url="https://kubernetes.io/docs/concepts/workloads/pods/#pod-templates",
            content="""apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: web
    tier: frontend
spec:
  containers:
  - name: nginx
    image: nginx:1.25.4-alpine
    ports:
    - containerPort: 80
      name: http
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "250m"
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 3
      periodSeconds: 5
""",
            description="Canonical single-container Pod manifest with health probes and resource limits.",
        ),
        K8sManifest(
            kind="Pod",
            api_version="v1",
            name="multi-container-sidecar-pod",
            source_file="content/en/examples/pods/two-container-pod.yaml",
            url="https://kubernetes.io/docs/concepts/workloads/pods/#multi-container-pods",
            content="""apiVersion: v1
kind: Pod
metadata:
  name: app-with-sidecar
  labels:
    app: order-processor
spec:
  restartPolicy: Always
  volumes:
  - name: shared-logs
    emptyDir: {}
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "while true; do echo $(date) 'Order processed' >> /var/log/app.log; sleep 2; done"]
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log
  - name: log-shipper-sidecar
    image: busybox:1.36
    command: ["sh", "-c", "tail -n+1 -F /var/log/app.log"]
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log
""",
            description="Canonical multi-container Pod with shared emptyDir volume (Sidecar logging pattern).",
        ),
        K8sManifest(
            kind="Pod",
            api_version="v1",
            name="pod-with-config-and-secret",
            source_file="content/en/examples/pods/pod-configmap-secret.yaml",
            url="https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/",
            content="""apiVersion: v1
kind: Pod
metadata:
  name: secured-app-pod
spec:
  containers:
  - name: backend
    image: python:3.11-slim
    env:
    - name: APP_MODE
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: mode
    - name: DATABASE_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: password
    resources:
      requests:
        memory: "128Mi"
        cpu: "150m"
      limits:
        memory: "256Mi"
        cpu: "500m"
""",
            description="Canonical Pod demonstrating ConfigMap and Secret injection via valueFrom.",
        ),
        K8sManifest(
            kind="Service",
            api_version="v1",
            name="web-service",
            source_file="content/en/examples/service/web-service.yaml",
            url="https://kubernetes.io/docs/concepts/services-networking/service/#defining-a-service",
            content="""apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
""",
            description="Canonical ClusterIP Service routing traffic to pods with label app: web.",
        ),
    ]
