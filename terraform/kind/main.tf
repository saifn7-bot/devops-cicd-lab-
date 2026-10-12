terraform {
  required_version = ">= 1.5.0"
  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = ">= 0.4.0"
    }
  }
}

provider "kind" {}

resource "kind_cluster" "lab" {
  name            = "devops-lab"
  wait_for_ready  = true
  kubeconfig_path = pathexpand("~/.kube/devops-lab.kubeconfig")

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"
      extra_port_mappings {
        container_port = 30080
        host_port      = 30080
      }
    }

    node {
      role = "worker"
    }
  }
}

output "cluster_name" {
  value = kind_cluster.lab.name
}

output "kubeconfig_path" {
  value = kind_cluster.lab.kubeconfig_path
}
