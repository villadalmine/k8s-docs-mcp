import pytest
from k8s_docs_mcp.server import search_k8s_docs, get_canonical_manifest, list_supported_resources


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


if __name__ == "__main__":
    print("Testing search_k8s_docs:")
    print(search_k8s_docs("network policies")[:300])
    print("\nTesting get_canonical_manifest:")
    print(get_canonical_manifest("NetworkPolicy")[:300])
    print("\nTesting list_supported_resources:")
    print(list_supported_resources())
    print("\nAll unit smoke tests passed!")
