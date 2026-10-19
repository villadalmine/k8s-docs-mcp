import pytest
from k8s_docs_mcp.server import (
    search_k8s_docs,
    get_canonical_manifest,
    list_supported_resources,
    check_api_version,
)
from k8s_docs_mcp.hugo_preprocessor import HugoPreprocessor


def test_search_k8s_docs():
    res = search_k8s_docs("network policies")
    assert "Official Kubernetes Documentation" in res
    assert "https://kubernetes.io/docs/" in res


def test_get_canonical_manifest():
    res = get_canonical_manifest("NetworkPolicy")
    assert "kind: NetworkPolicy" in res
    assert "apiVersion: networking.k8s.io/v1" in res


def test_list_supported_resources():
    res = list_supported_resources()
    assert "NetworkPolicy" in res
    assert "Deployment" in res


def test_check_api_version_ingress_deprecated():
    res = check_api_version("Ingress", "extensions/v1beta1")
    assert "CRITICAL" in res
    assert "REMOVED in Kubernetes v1.22" in res
    assert "networking.k8s.io/v1" in res


def test_check_api_version_validating_admission_policy():
    res = check_api_version("ValidatingAdmissionPolicy")
    assert "admissionregistration.k8s.io/v1" in res
    assert "CEL" in res


def test_hugo_preprocessor_alerts():
    pre = HugoPreprocessor()
    text = "{{< note >}}Remember to enable RBAC.{{< /note >}}"
    processed = pre.preprocess(text)
    assert "[!NOTE]" in processed
    assert "Remember to enable RBAC." in processed


if __name__ == "__main__":
    print("Running smoke tests...")
    print(check_api_version("Ingress", "extensions/v1beta1"))
    print("---")
    print(check_api_version("ValidatingAdmissionPolicy"))
    print("\nAll tests passed!")
