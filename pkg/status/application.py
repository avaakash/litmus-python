"""
    application package
"""


import time
import logging

from pkg.utils.annotation import annotation


class Application(object):
    """ Application class is checking the status of application """

    def AUTStatusCheck(self, appNs, appLabel, containerName, timeout, delay, chaosDetails, clients):
        """
            AUTStatusCheck checks the status of application under test
            If annotationCheck is true, it will check the status of the annotated pod only
            else it will check status of all pods with matching label
        """

        if chaosDetails.AppDetail.AnnotationCheck:
            logging.info("[Info]: Check Annotated for Applications Status")
            err = self.AnnotatedApplicationsStatusCheck(
                clients, appNs, appLabel, containerName, chaosDetails, 0, timeout, delay)
            if err is not None:
                return err
        else:
            if appLabel == "":
                # Checking whether applications are healthy
                logging.info(
                    "[status]: No appLabels provided, skipping the application status checks")
            else:
                # Checking whether application containers are in ready state
                logging.info(
                    "[status]: Checking whether application containers are in ready state")
                err = self.CheckContainerStatus(
                    clients, appNs, appLabel, containerName, 0, timeout, delay)
                if err is not None:
                    return err

                # Checking whether application pods are in running state
                logging.info(
                    "[status]: Checking whether application pods are in running state")
                err = self.CheckPodStatus(
                    clients, appNs, appLabel, 0, timeout, delay)
                if err is not None:
                    return err
        return None

    def AnnotatedApplicationsStatusCheck(self, clients, appNs, appLabel, containerName, chaosDetails, init, timeout, delay):
        """ AnnotatedApplicationsStatusCheck checks the status of all the annotated applications with matching label """

        try:
            podList = clients.clientCoreV1.list_namespaced_pod(
                appNs, label_selector=appLabel)
            if len(podList.items) == 0:
                raise Exception("Unable to find the pods with matching labels")
            for pod in podList.items:
                parentName, err = annotation.GetParentName(
                    clients, pod, chaosDetails)
                if err is not None:
                    return err
                isParentAnnotated, err = annotation.IsParentAnnotated(
                    clients, parentName, chaosDetails)
                if err is not None:
                    raise Exception(
                        f"Unable to find the pods with Annotation :{chaosDetails.AppDetail.AnnotationValue}")

                if isParentAnnotated:
                    if containerName == "":
                        for container in pod.status.container_statuses:
                            if container.state.terminated is not None:
                                raise Exception(
                                    "Container is in terminated state")

                            if not container.ready:
                                raise Exception(
                                    "containers are not yet in running state")

                            logging.info(
                                "[status]: The Container status are as follows Container : %s, Pod : %s, Readiness : %s",
                                container.name, pod.metadata.name, container.ready)
                    else:
                        for container in pod.status.container_statuses:
                            if containerName == container.name:
                                if container.state.terminated is not None:
                                    raise Exception(
                                        "container is in terminated state")

                                if not container.ready:
                                    raise Exception(
                                        "containers are not yet in running state")
                                logging.info(
                                    "[status]: The Container status are as follows Container : %s, Pod : %s, Readiness : %s.",
                                    container.name, pod.metadata.name, container.ready)

                    if pod.status.phase != "Running":
                        raise Exception(
                            f"{pod.metadata.name} pod is not yet in running state")
                    logging.info(
                        "[status]: The status of Pods are as follows Pod : %s, status : %s.", pod.metadata.name, pod.status.phase)
        except Exception as exp:
            if init > timeout:
                return exp
            time.sleep(delay)
            return self.AnnotatedApplicationsStatusCheck(
                clients, appNs, appLabel, containerName, chaosDetails, init + delay, timeout, delay)

        return None

    def CheckApplicationStatus(self, appNs, appLabel, timeout, delay, clients):
        """ CheckApplicationStatus checks the status of the AUT """

        if appLabel == "":
            # Checking whether applications are healthy
            logging.info(
                "[status]: No appLabels provided, skipping the application status checks")
        else:
            # Checking whether application containers are in ready state
            logging.info(
                "[status]: Checking whether application containers are in ready state")
            err = self.CheckContainerStatus(
                clients, appNs, appLabel, "", 0, timeout, delay)
            if err is not None:
                return err

            # Checking whether application pods are in running state
            logging.info(
                "[status]: Checking whether application pods are in running state")
            err = self.CheckPodStatus(
                clients, appNs, appLabel, 0, timeout, delay)
            if err is not None:
                return err

        return None

    # CheckAuxiliaryApplicationStatus checks the status of the Auxiliary applications
    def CheckAuxiliaryApplicationStatus(self, AuxiliaryAppDetails, timeout, delay, clients):
        """ CheckAuxiliaryApplicationStatus checks the status of the Auxiliary applications """
        AuxiliaryAppInfo = AuxiliaryAppDetails.split(",")
        for val in AuxiliaryAppInfo:
            AppInfo = val.split(":")
            err = self.CheckApplicationStatus(
                AppInfo[0], AppInfo[1], timeout, delay, clients)
            if err is not None:
                return err

        return None

    def CheckPodStatusPhase(self, clients, appNs, appLabel, states, init, timeout, delay):
        """ CheckPodStatusPhase is helper to checks the running status of the application pod """

        try:
            podList = clients.clientCoreV1.list_namespaced_pod(
                appNs, label_selector=appLabel)
            if len(podList.items) == 0:
                return Exception(f"Unable to find the pods with matching labels, err: {appLabel}")
            for pod in podList.items:
                if str(pod.status.phase) != states:
                    raise Exception(f"Pod is not yet in {states} state(s)")

                logging.info("[status]: The status of Pods are as follows Pod : %s status : %s",
                             pod.metadata.name, pod.status.phase)
        except Exception as exp:
            if init > timeout:
                return ValueError(exp)
            time.sleep(delay)
            return self.CheckPodStatusPhase(clients, appNs, appLabel, states, init + delay, timeout, delay)

        return None

    def CheckPodStatus(self, clients, appNs, appLabel, tries, timeout, delay):
        """ CheckPodStatus checks the running status of the application pod """
        return self.CheckPodStatusPhase(clients, appNs, appLabel, "Running", tries, timeout, delay)

    def CheckContainerStatus(self, clients, appNs, appLabel, containerName, init, timeout, delay):
        """
            CheckContainerStatus checks the status of the application container for given timeout,
            if it does not match label it will
            retry for timeout time
        """
        try:
            podList = clients.clientCoreV1.list_namespaced_pod(
                appNs, label_selector=appLabel)
            if len(podList.items) == 0:
                raise Exception("Unable to find the pods with matching labels")

            for pod in podList.items:
                if containerName == "":
                    err = self.validateAllContainerStatus(
                        pod.metadata.name, pod.status.container_statuses)
                    if err is not None:
                        raise Exception(err)
                else:
                    err = self.validateContainerStatus(
                        containerName, pod.metadata.name, pod.status.container_statuses)
                    if err is not None:
                        raise Exception(err)
        except Exception as exp:
            if init > timeout:
                return ValueError(exp)
            time.sleep(delay)
            return self.CheckContainerStatus(clients, appNs, appLabel, containerName, init + delay, timeout, delay)

        return None

    def validateContainerStatus(self, containerName, podName, ContainerStatuses):
        """ validateContainerStatus verify that the provided container should be in ready state """
        for container in ContainerStatuses:
            if container.name == containerName:
                if container.state.terminated is not None:
                    return ValueError("container is in terminated state")
                if not container.ready:
                    return ValueError("containers are not yet in running state")

                logging.info("[status]: The Container status are as follows Container : %s, Pod : %s, Readiness : %s",
                             container.name, podName, container.ready)
        return None

    def validateAllContainerStatus(self, podName, ContainerStatuses):
        """ validateAllContainerStatus verify that the all the containers should be in ready state """
        for container in ContainerStatuses:
            err = self.validateContainerStatus(
                container.name, podName, ContainerStatuses)
            if err is not None:
                return ValueError(err)
        return None
