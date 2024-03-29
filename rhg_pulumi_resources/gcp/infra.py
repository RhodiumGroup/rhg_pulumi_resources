import pulumi
import pulumi_gcp as gcp
from pulumi_kubernetes.core.v1 import ServiceAccount


TYPE_PACKAGE_NAME = "rhg"
TYPE_INDEX_NAME = "gcp"


def pulumi_type_name(component, package, index=None):
    """Get Pulumi-style resource type names.

    Names are like ``{package}:{index}:{component}``.

    Parameters
    ----------
    component : str
        Resource component name. Usually camel-case name of resource class. In
        other words, ``self.__class__.__name__`` if used within a class.
    package : str
        Usually a base library or package name.
    index : str or None, optional
        Usually module name. If unspecified, uses ``__name__``.

    Return
    ------
    str
    """
    if index is None:
        index = __name__
    return f"{package}:{index}:{component}"


class WorkerPoolCluster(pulumi.ComponentResource):
    def __init__(
        self,
        resource_name,
        *,
        machinetype_core="n1-standard-4",
        machinetype_worker="n1-highmem-8",
        disk_size_gb_core=100.0,
        disk_size_gb_worker=100.0,
        disktype_core="pd-standard",
        disktype_worker="pd-standard",
        nodecountminmax_core=(0, 5),
        nodecountminmax_worker=(0, 10),
        preemptible_core=False,
        preemptible_worker=True,
        image_type=None,
        min_cluster_version=None,
        release_channel=None,
        oauthscopes=None,
        enable_servicemesh=False,
        opts=None,
    ):
        """Vanilla Google Kubernetes Engine (GKE) worker cluster with core node.

        Cluster includes GKE istio and default configuration for GKE Workload Identity.

        There are two node pools: a default "core" and one worker pool. The
        worker node pool is preemptible. The worker node pool also has two
        taints ``NO_SCHEDULE`` taint ``dedicated=worker`` and a ``NO_SCHEDULE``
        ``preemptible=true`` taint.

        Parameters
        ----------
        resource_name : str
        machinetype_core : str, optional
        machinetype_worker : str, optional
        disk_size_gb_core : float, optional
        disk_size_gb_worker : float, optional
        disktype_core : str, optional
        disktype_worker : str, optional
        nodecountminmax_core : Sequence[int], optional
        nodecountminmax_worker : Sequence[int], optional
        preemptible_core : bool, optional
        preemptible_worker : bool, optional
        image_type : str, optional
            Core and worker node image type.
        min_cluster_version : str or None, optional
            Minimum Kubernetes version for the master node. If ``None``, uses the
            default version on GKE.
        release_channel : dict or None, optional
            Passed to pulumi_gcp.container.Cluster.
        oauthscopes : Sequence of str or None, optional
            OAuth scopes for node pools. If ``None``, uses default scopes as defined
            https://cloud.google.com/sdk/gcloud/reference/container/clusters/create#--scopes.
        enable_servicemesh : bool, optional
            Enable default GKE Istio service mesh.
        opts : pulumi.ResourceOptions or None, optional

        Attributes
        ----------
        cluster : pulumi_gcp.container.Cluster
        nodepool_core : pulumi_gcp.container.NodePool
        nodepool_worker : pulumi_gcp.container.NodePool
        """
        resource_type = pulumi_type_name(
            self.__class__.__name__, TYPE_PACKAGE_NAME, index=TYPE_INDEX_NAME
        )
        super().__init__(resource_type, resource_name, None, opts)

        if oauthscopes is None:
            # This is GKE default scopes for a new cluster as of 2020-06-11.
            oauthscopes = [
                "https://www.googleapis.com/auth/devstorage.read_only",
                "https://www.googleapis.com/auth/logging.write",
                "https://www.googleapis.com/auth/monitoring",
                "https://www.googleapis.com/auth/service.management.readonly",
                "https://www.googleapis.com/auth/servicecontrol",
                "https://www.googleapis.com/auth/trace.append",
            ]

        common_resource_labels = {
            "managed-by": "pulumi",
            "env": pulumi.get_stack(),
            "pulumi-project": pulumi.get_project(),
        }

        core_resource_labels = common_resource_labels.copy()

        self.cluster = gcp.container.Cluster(
            resource_name,
            min_master_version=min_cluster_version,
            maintenance_policy={
                "recurringWindow": {
                    "startTime": "2020-01-05T12:00:00Z",
                    "endTime": "2020-01-06T12:00:00Z",
                    "recurrence": "FREQ=WEEKLY",
                }
            },
            resource_labels=core_resource_labels,
            release_channel=release_channel,
            initial_node_count=1,
            remove_default_node_pool=True,
            workload_identity_config={
                "identityNamespace": "{}.svc.id.goog".format(
                    pulumi.Config("gcp").get("project")
                )
            },
            addons_config={
                "istioConfig": {
                    "disabled": not enable_servicemesh,
                }
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

        core_resource_labels = common_resource_labels.copy()
        if preemptible_core:
            core_resource_labels["preemptible"] = str(preemptible_core).lower()

        self.nodepool_core = gcp.container.NodePool(
            "nodepool-core",
            cluster=self.cluster.name,
            autoscaling={
                "maxNodeCount": int(nodecountminmax_core[1]),
                "minNodeCount": int(nodecountminmax_core[0]),
            },
            initial_node_count=1,
            management={"autoRepair": True, "autoUpgrade": True},
            node_config={
                "image_type": image_type,
                "disk_size_gb": disk_size_gb_core,
                "diskType": disktype_core,
                "machine_type": machinetype_core,
                "labels": core_resource_labels,
                "oauthScopes": oauthscopes,
                "preemptible": bool(preemptible_core),
                "workloadMetadataConfig": {"nodeMetadata": "GKE_METADATA_SERVER"},
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

        worker_resource_labels = common_resource_labels.copy()
        worker_resource_labels["dedicated"] = "worker"
        if preemptible_worker:
            worker_resource_labels["preemptible"] = str(preemptible_worker).lower()

        self.nodepool_worker = gcp.container.NodePool(
            "nodepool-worker",
            cluster=self.cluster.name,
            autoscaling={
                "maxNodeCount": int(nodecountminmax_worker[1]),
                "minNodeCount": int(nodecountminmax_worker[0]),
            },
            initial_node_count=1,
            management={"autoRepair": True, "autoUpgrade": True},
            node_config={
                "image_type": image_type,
                "disk_size_gb": disk_size_gb_worker,
                "diskType": disktype_worker,
                "labels": worker_resource_labels,
                "machine_type": machinetype_worker,
                "oauthScopes": oauthscopes,
                "preemptible": bool(preemptible_worker),
                "taints": [
                    {"key": "dedicated", "value": "worker", "effect": "NO_SCHEDULE"}
                ],
                # Below needed to prevent nodedpool from always replacing on deploy.
                "workloadMetadataConfig": {"nodeMetadata": "GKE_METADATA_SERVER"},
            },
            opts=pulumi.ResourceOptions(parent=self),
        )


class WorkloadIdentity(pulumi.ComponentResource):
    def __init__(
        self,
        resource_name,
        gcp_account_id,
        k8s_sa_name,
        k8s_provider,
        gcp_display_name=None,
        opts=None,
    ):
        """Create a GKE Workload Identity, binding Kubernetes and GCP service accounts

        This assumes that Workload Identity has already been enabled for the cluster.

        Parameters
        ----------
        resource_name : str
        gcp_account_id : str
        k8s_sa_name : str
        k8s_provider : pulumi_kubernetes.provider.Provider
        gcp_display_name : str or None, optional
        opts : pulumi.ResourceOptions or None, optional

        Attributes
        ----------
        gcp_serviceaccount : pulumi_gcp.serviceaccount.Account
        k8s_serviceaccount : pulumi_kubernetes.core.v1.ServiceAccount
        sa_binding_iammember : pulumi_gcp.serviceaccount.IAMMember
        """
        resource_type = pulumi_type_name(
            self.__class__.__name__, TYPE_PACKAGE_NAME, index=TYPE_INDEX_NAME
        )
        super().__init__(resource_type, resource_name, None, opts)

        if gcp_display_name is None:
            gcp_display_name = gcp_account_id

        self.gcp_serviceaccount = gcp.serviceaccount.Account(
            f"{resource_name}-gcp-serviceaccount",
            account_id=gcp_account_id,
            display_name=gcp_display_name,
            description=f"Managed by pulumi project {pulumi.get_project()} ({pulumi.get_stack()})",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.k8s_serviceaccount = ServiceAccount(
            f"{resource_name}-k8s-serviceaccount",
            metadata={
                "name": k8s_sa_name,
                "labels": {
                    "env": pulumi.get_stack(),
                    "pulumi-project": pulumi.get_project(),
                    "managed-by": "pulumi",
                },
                # Append annotation as final step to GSA-KSA SA binding.
                "annotations": {
                    "iam.gke.io/gcp-service-account": self.gcp_serviceaccount.email
                },
            },
            opts=pulumi.ResourceOptions(provider=k8s_provider, parent=self),
        )

        # IAM to bind KSA and GSA fastimpact SAs
        ksa_gsa_binding_member = pulumi.Output.all(
            self.gcp_serviceaccount.project, self.k8s_serviceaccount.metadata
        ).apply(
            lambda x: f"serviceAccount:{x[0]}.svc.id.goog[{x[1].get('namespace')}/{x[1].get('name')}]"
        )

        sa_full_id = pulumi.Output.all(
            self.gcp_serviceaccount.project, self.gcp_serviceaccount.email
        ).apply(lambda x: "projects/{}/serviceAccounts/{}".format(*x))

        self.sa_binding_iammember = gcp.serviceaccount.IAMMember(
            f"{resource_name}-sa-binding-iammember",
            service_account_id=sa_full_id,
            member=ksa_gsa_binding_member,
            role="roles/iam.workloadIdentityUser",
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.gcp_serviceaccount, self.k8s_serviceaccount],
            ),
        )
