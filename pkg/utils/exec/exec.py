"""
    exec pacakge
"""


from kubernetes.stream import stream


class PodDetails(object):
    """ PodDetails contains all the required variables to exec inside a container """

    def __init__(self, PodName=None, Namespace=None, ContainerName=None):
        self.PodName = PodName
        self.Namespace = Namespace
        self.ContainerName = ContainerName


def checkPodStatus(pod, containerName):
    """ checkPodStatus verify the status of given pod & container """

    if pod.status.phase.lower() != "running":
        return ValueError(f"{pod.Name} pod is not in running state, phase: {pod.Status.Phase}")

    for container in pod.status.container_statuses:
        if container.name == containerName and not container.ready:
            return ValueError(
                f"{container.name} container of {pod.metadata.name} pod is not in ready state, phase: {pod.status.phase}")

    return None


def Exec(commandDetails, clients, command):
    """ Exec will execute the given command in the given container of the given pod """
    try:
        pod = clients.clientCoreV1.read_namespaced_pod(
            name=commandDetails.PodName, namespace=commandDetails.Namespace)
    except Exception as exp:
        return "", ValueError(f"unable to get {commandDetails.PodName} pod in {commandDetails.Namespace} namespace, err: {exp}")

    err = checkPodStatus(pod, commandDetails.ContainerName)
    if err is not None:
        return "", err

    # Calling exec and waiting for response
    stream(clients.clientCoreV1.connect_get_namespaced_pod_exec,
           commandDetails.PodName,
           commandDetails.Namespace,
           command=command,
           stderr=True, stdin=False,
           stdout=True, tty=False)

    return None


def SetExecCommandAttributes(podDetails, PodName, ContainerName, Namespace):
    """ SetExecCommandAttributes initialise all the pod details  to run exec command """

    podDetails.ContainerName = ContainerName
    podDetails.Namespace = Namespace
    podDetails.PodName = PodName
