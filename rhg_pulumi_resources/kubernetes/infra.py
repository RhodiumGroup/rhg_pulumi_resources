import pulumi
from pulumi_kubernetes.yaml import ConfigFile


TYPE_PACKAGE_NAME = "rhg"
TYPE_INDEX_NAME = "kubernetes"


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


class ArgoWorkflow(pulumi.ComponentResource):
    def __init__(self, resource_name, k8s_provider, argo_version=None, opts=None):
        """Argo workflow CRDs, services, etc, installed for cluster-wide use.

        This assumes the ``argo`` namespace has already been made.

        Parameters
        ----------
        resource_name : str
        k8s_provider : pulumi_kubernetes.provider.Provider
            Must be for the argo namespace.
        argo_version : str or None, optional
            Argo version to install. If ``None``, installs "stable".
        opts : pulumi.ResourceOptions or None, optional

        Attributes
        ----------
        configfile : pulumi_kubernetes.yaml.ConfigFile
        """
        if argo_version is None:
            argo_version = "stable"

        resource_type = pulumi_type_name(
            self.__class__.__name__, TYPE_PACKAGE_NAME, index=TYPE_INDEX_NAME
        )
        super().__init__(resource_type, resource_name, None, opts)

        # Directly install the latest argo-workflow manifests
        self.configfile = ConfigFile(
            name=f"{resource_name}-configfile",
            file_id=f"https://raw.githubusercontent.com/argoproj/argo-workflows/{argo_version}/manifests/install.yaml",
            opts=pulumi.ResourceOptions(provider=k8s_provider, parent=self),
        )
