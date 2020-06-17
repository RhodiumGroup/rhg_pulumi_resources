import pulumi


def _kubectl_config_callback(proj, loc, cname, master_auth, endpoint):
    context = f"gke_{proj}_{loc}_{cname}"
    config = f"""apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: {master_auth}
    server: https://{endpoint}
  name: {context}
contexts:
- context:
    cluster: {context}
    user: {context}
  name: {context}
current-context: {context}
kind: Config
preferences: {{}}
users:
- name: {context}
  user:
    auth-provider:
      config:
        cmd-args: config config-helper --format=json
        cmd-path: gcloud
        expiry-key: '{{.credential.token_expiry}}'
        token-key: '{{.credential.access_token}}'
      name: gcp
    """
    return config


def build_kubectl_config(cluster):
    """Generates GKE kubectl auth config yaml-like string on the fly

    Parameters
    ----------
    cluster : pulumi_gcp.container.Cluster

    Returns
    -------
    str
    """
    conf = pulumi.Output.all(
        cluster.project,
        cluster.location,
        cluster.name,
        cluster.master_auth["clusterCaCertificate"],
        cluster.endpoint,
    ).apply(lambda x: _kubectl_config_callback(*x))
    return conf
