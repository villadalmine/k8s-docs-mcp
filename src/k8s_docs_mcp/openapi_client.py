from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class ApiVersionInfo:
    kind: str
    current_api_version: str
    status: str  # "stable", "beta", "deprecated", "removed"
    deprecated_versions: List[str]
    removed_in: Optional[str] = None
    replacement: Optional[str] = None
    notes: str = ""


# Authoritative Kubernetes OpenAPI / API Registry
OFFICIAL_K8S_API_REGISTRY: Dict[str, ApiVersionInfo] = {
    "ingress": ApiVersionInfo(
        kind="Ingress",
        current_api_version="networking.k8s.io/v1",
        status="stable",
        deprecated_versions=["extensions/v1beta1", "networking.k8s.io/v1beta1"],
        removed_in="v1.22",
        replacement="networking.k8s.io/v1",
        notes="Migrate to networking.k8s.io/v1. The pathType field (Prefix, Exact, ImplementationSpecific) is mandatory.",
    ),
    "podsecuritypolicy": ApiVersionInfo(
        kind="PodSecurityPolicy",
        current_api_version="policy/v1beta1 (REMOVED)",
        status="removed",
        deprecated_versions=["policy/v1beta1", "extensions/v1beta1"],
        removed_in="v1.25",
        replacement="PodSecurityStandards (pod-security.kubernetes.io labels) or ValidatingAdmissionPolicy",
        notes="PodSecurityPolicy was fully removed in Kubernetes v1.25. Use built-in Pod Security Admission labels or in-tree CEL ValidatingAdmissionPolicy.",
    ),
    "networkpolicy": ApiVersionInfo(
        kind="NetworkPolicy",
        current_api_version="networking.k8s.io/v1",
        status="stable",
        deprecated_versions=["extensions/v1beta1"],
        removed_in="v1.16",
        replacement="networking.k8s.io/v1",
        notes="Always use networking.k8s.io/v1.",
    ),
    "validatingadmissionpolicy": ApiVersionInfo(
        kind="ValidatingAdmissionPolicy",
        current_api_version="admissionregistration.k8s.io/v1",
        status="stable",
        deprecated_versions=["admissionregistration.k8s.io/v1beta1", "admissionregistration.k8s.io/v1alpha1"],
        removed_in=None,
        replacement=None,
        notes="GA in Kubernetes v1.30 via admissionregistration.k8s.io/v1. Enables declarative in-tree CEL validation without webhook network latency.",
    ),
    "validatingadmissionpolicybinding": ApiVersionInfo(
        kind="ValidatingAdmissionPolicyBinding",
        current_api_version="admissionregistration.k8s.io/v1",
        status="stable",
        deprecated_versions=["admissionregistration.k8s.io/v1beta1"],
        removed_in=None,
        replacement=None,
        notes="GA in Kubernetes v1.30. Binds a ValidatingAdmissionPolicy to namespaces or specific resources.",
    ),
    "validatingwebhookconfiguration": ApiVersionInfo(
        kind="ValidatingWebhookConfiguration",
        current_api_version="admissionregistration.k8s.io/v1",
        status="stable",
        deprecated_versions=["admissionregistration.k8s.io/v1beta1"],
        removed_in="v1.22",
        replacement="admissionregistration.k8s.io/v1",
        notes="admissionregistration.k8s.io/v1 requires sideEffects: None or NoneOnDryRun and admissionReviewVersions: ['v1'].",
    ),
    "mutatingwebhookconfiguration": ApiVersionInfo(
        kind="MutatingWebhookConfiguration",
        current_api_version="admissionregistration.k8s.io/v1",
        status="stable",
        deprecated_versions=["admissionregistration.k8s.io/v1beta1"],
        removed_in="v1.22",
        replacement="admissionregistration.k8s.io/v1",
        notes="admissionregistration.k8s.io/v1 requires sideEffects: None or NoneOnDryRun and admissionReviewVersions: ['v1'].",
    ),
    "cronjob": ApiVersionInfo(
        kind="CronJob",
        current_api_version="batch/v1",
        status="stable",
        deprecated_versions=["batch/v1beta1"],
        removed_in="v1.25",
        replacement="batch/v1",
        notes="batch/v1beta1 was removed in v1.25. Use batch/v1.",
    ),
    "horizontalpodautoscaler": ApiVersionInfo(
        kind="HorizontalPodAutoscaler",
        current_api_version="autoscaling/v2",
        status="stable",
        deprecated_versions=["autoscaling/v2beta1", "autoscaling/v2beta2"],
        removed_in="v1.25",
        replacement="autoscaling/v2",
        notes="autoscaling/v2beta1 and v2beta2 were removed in v1.25. Use autoscaling/v2.",
    ),
    "deployment": ApiVersionInfo(
        kind="Deployment",
        current_api_version="apps/v1",
        status="stable",
        deprecated_versions=["extensions/v1beta1", "apps/v1beta1", "apps/v1beta2"],
        removed_in="v1.16",
        replacement="apps/v1",
        notes="Always use apps/v1.",
    ),
    "statefulset": ApiVersionInfo(
        kind="StatefulSet",
        current_api_version="apps/v1",
        status="stable",
        deprecated_versions=["apps/v1beta1", "apps/v1beta2"],
        removed_in="v1.16",
        replacement="apps/v1",
        notes="Always use apps/v1.",
    ),
    "daemonset": ApiVersionInfo(
        kind="DaemonSet",
        current_api_version="apps/v1",
        status="stable",
        deprecated_versions=["extensions/v1beta1", "apps/v1beta1"],
        removed_in="v1.16",
        replacement="apps/v1",
        notes="Always use apps/v1.",
    ),
    "customresourcedefinition": ApiVersionInfo(
        kind="CustomResourceDefinition",
        current_api_version="apiextensions.k8s.io/v1",
        status="stable",
        deprecated_versions=["apiextensions.k8s.io/v1beta1"],
        removed_in="v1.22",
        replacement="apiextensions.k8s.io/v1",
        notes="apiextensions.k8s.io/v1 requires structural OpenAPI v3 schemas in spec.versions[*].schema.openAPIV3Schema.",
    ),
}


class K8sApiRegistry:
    """Provides deterministic, authoritative API validation based on official Kubernetes OpenAPI specs."""

    @staticmethod
    def check_resource(kind: str, query_api_version: Optional[str] = None) -> Dict[str, Any]:
        """Checks API version validity, deprecation, and replacements for a Kubernetes Kind."""
        key = kind.strip().lower()
        info = OFFICIAL_K8S_API_REGISTRY.get(key)
        if not info:
            return {
                "kind": kind,
                "found": False,
                "message": f"Kind '{kind}' is not in the core API registry. Check spelling or verify if it belongs to a CustomResourceDefinition (CRD).",
            }

        is_deprecated = False
        is_removed = False
        warning = None

        if query_api_version:
            clean_ver = query_api_version.strip()
            if clean_ver in info.deprecated_versions:
                is_deprecated = True
                if info.removed_in:
                    is_removed = True
                    warning = f"CRITICAL: '{clean_ver}' was REMOVED in Kubernetes {info.removed_in}. It will fail admission on modern clusters."
                else:
                    warning = f"WARNING: '{clean_ver}' is DEPRECATED. Use '{info.current_api_version}' instead."
            elif clean_ver != info.current_api_version and info.status != "removed":
                warning = f"Notice: You provided '{clean_ver}'. The current authoritative stable version is '{info.current_api_version}'."

        return {
            "kind": info.kind,
            "found": True,
            "current_api_version": info.current_api_version,
            "status": info.status,
            "deprecated_versions": info.deprecated_versions,
            "removed_in": info.removed_in,
            "recommended_replacement": info.replacement,
            "warning": warning,
            "notes": info.notes,
        }
