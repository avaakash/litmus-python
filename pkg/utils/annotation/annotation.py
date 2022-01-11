"""
    annotation package
"""


def getDeploymentName(targetPod, chaosDetails, clients):
    """
        getDeploymentName derive the deployment name belongs to the given target pod
        it extract the parent name from the owner references
    """
    rsOwnerRef = targetPod.metadata.owner_references
    for own in rsOwnerRef:
        if own.kind == "ReplicaSet":
            try:
                rs = clients.clientApps.read_namespaced_replica_set(
                    own.name, chaosDetails.AppDetail.Namespace)
            except Exception as exp:
                return "", exp
            ownerRef = rs.metadata.owner_references
            for own in ownerRef:
                if own.kind == "Deployment":
                    return own.name, None

    return "", ValueError(f"no deployment found for {targetPod.Name} pod")


def getStatefulsetName(targetPod):
    """
        getStatefulsetName derive the statefulset name belongs to the given target pod
        it extract the parent name from the owner references
    """

    ownerRef = targetPod.metadata.owner_references
    for own in ownerRef:
        if own.kind == "StatefulSet":
            return own.name, None

    return "", ValueError(f"no statefulset found for {targetPod.Name} pod")


def getDaemonsetName(targetPod):
    """
        getDaemonsetName derive the daemonset name belongs to the given target pod
        it extract the parent name from the owner references
    """

    ownerRef = targetPod.metadata.owner_references
    for own in ownerRef:
        if own.kind == "DaemonSet":
            return own.name, None

    return "", ValueError(f"no daemonset found for {targetPod.Name} pod")


def getDeploymentConfigName(targetPod, chaosDetails, clients):
    """
        getDeploymentConfigName derive the deploymentConfig name belongs to the given target pod
        it extract the parent name from the owner references
    """

    rcOwnerRef = targetPod.metadata.owner_references
    for own in range(rcOwnerRef):
        if own.kind == "ReplicationController":
            try:
                rc = clients.clientCoreV1.read_namespaced_replication_controller(
                    own.name, chaosDetails.AppDetail.Namespace)
            except Exception as exp:
                return "", exp

            ownerRef = rc.metadata.owner_references
            for own in ownerRef:
                if own.kind == "DeploymentConfig":
                    return own.name, None
    return "", ValueError(f"No deploymentConfig found for {targetPod.Name} pod")


def getRolloutName(targetPod, chaosDetails, clients):
    """
        getDeploymentConfigName derive the rollout name belongs to the given target pod
        it extract the parent name from the owner references
    """

    rsOwnerRef = targetPod.metadata.owner_references
    for own in rsOwnerRef:
        if own.kind == "ReplicaSet":
            try:
                rs = clients.clientApps.read_namespaced_replica_set(
                    own.name, chaosDetails.AppDetail.Namespace)
            except Exception as exp:
                return "", exp

            ownerRef = rs.metadata.owner_references
            for own in ownerRef:
                if own.kind == "Rollout":
                    return own.name, None
    return "", ValueError(f"no rollout found for {targetPod.Name} pod")


def GetParentName(clients, targetPod, chaosDetails):
    """ GetParentName derive the parent name of the given target pod """

    kind = chaosDetails.AppDetail.Kind
    if kind in ("deployment", "deployments"):
        return getDeploymentName(targetPod, chaosDetails, clients)
    if kind in ("statefulset", "statefulsets"):
        return getStatefulsetName(targetPod)
    if kind in ("daemonset", "daemonsets"):
        return getDaemonsetName(targetPod)
    if kind in ("deploymentConfig", "deploymentConfigs"):
        return getDeploymentConfigName(targetPod, chaosDetails, clients)
    if kind in ("rollout", "rollouts"):
        return getRolloutName(targetPod, chaosDetails, clients)
    return False,  ValueError(f"Appkind: {kind} is not supported")


def IsParentAnnotated(clients, parentName, chaosDetails):
    """ IsParentAnnotated check whether the target pod's parent is annotated or not """
    if chaosDetails.AppDetail.Kind.lower() == "deployment" or chaosDetails.AppDetail.Kind.lower() == "deployments":
        try:
            deploy = clients.clientApps.read_namespaced_deployment(
                name=parentName, namespace=chaosDetails.AppDetail.Namespace)
        except Exception as exp:
            return False, exp
        if deploy.metadata.annotations.get(chaosDetails.AppDetail.AnnotationKey) == chaosDetails.AppDetail.AnnotationValue:
            return True, None

    elif chaosDetails.AppDetail.Kind.lower() == "statefulset" or chaosDetails.AppDetail.Kind.lower() == "statefulsets":
        try:
            sts = clients.clientApps.read_namespaced_stateful_set(
                name=parentName, namespace=chaosDetails.AppDetail.Namespace)
        except Exception as exp:
            return False, exp

        if sts.metadata.annotations.get(chaosDetails.AppDetail.AnnotationKey) == chaosDetails.AppDetail.AnnotationValue:
            return True, None

    elif chaosDetails.AppDetail.Kind.lower() == "daemonset" or chaosDetails.AppDetail.Kind.lower() == "daemonsets":
        try:
            ds = clients.clientApps.read_namespaced_daemon_set(
                name=parentName, namespace=chaosDetails.AppDetail.Namespace)
        except Exception as exp:
            return False, exp

        if ds.metadata.annotations.get(chaosDetails.AppDetail.AnnotationKey) == chaosDetails.AppDetail.AnnotationValue:
            return True, None

    elif chaosDetails.AppDetail.Kind.lower() == "deploymentconfig":
        try:
            dc = clients.clientDyn.resources.get(api_version="v1", kind="DeploymentConfig", group="apps.openshift.io").get(
                namespace=chaosDetails.AppDetail.Namespace, name=parentName)
        except Exception as exp:
            return False, exp

        if dc.metadata.annotations.get(chaosDetails.AppDetail.AnnotationKey) == chaosDetails.AppDetail.AnnotationValue:
            return True, None

    elif chaosDetails.AppDetail.Kind.lower() == "rollout":
        try:
            ro = clients.clientDyn.resources.get(api_version="v1alpha1", kind="Rollout", group="argoproj.io").get(
                namespace=chaosDetails.AppDetail.Namespace, name=parentName)
        except Exception as exp:
            return "", exp

        if ro.metadata.annotations.get(chaosDetails.AppDetail.AnnotationKey) == chaosDetails.AppDetail.AnnotationValue:
            return True, None

    else:
        return False, ValueError(f"{chaosDetails.AppDetail.Kind} appkind is not supported")

    return False, None
