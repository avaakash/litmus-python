"""
    Chaoslib for pod-delete experiment
"""
import logging
from datetime import datetime

from pkg.types import types
from pkg.events import events
from pkg.utils.common import common, pods
from pkg.status import application as status
from pkg.maths import maths


def PreparePodDelete(experimentsDetails, eventsDetails, chaosDetails, clients):
    """PreparePodDelete contains the prepration steps before chaos injection"""

    #Waiting for the ramp time before chaos injection
    if experimentsDetails.RampTime != 0:
        logging.info("[Ramp]: Waiting for the %s ramp time before injecting chaos",
                     experimentsDetails.RampTime)
        common.WaitForDuration(experimentsDetails.RampTime)
    # mode for chaos injection
    if experimentsDetails.Sequence.lower() == "serial":
        err = injectChaosInSerialMode(
            experimentsDetails, chaosDetails, eventsDetails, clients)
        if err is not None:
            return err
    elif experimentsDetails.Sequence.lower() == "parallel":
        err = injectChaosInParallelMode(
            experimentsDetails, chaosDetails, eventsDetails, clients)
        if err is not None:
            return err
    else:
        return ValueError(f"{experimentsDetails.Sequence} sequence is not supported")

    #Waiting for the ramp time after chaos injection
    if experimentsDetails.RampTime != 0:
        logging.info(
            "[Ramp]: Waiting for the %s ramp time after injecting chaos", experimentsDetails.RampTime)
        common.WaitForDuration(experimentsDetails.RampTime)

    return None


def injectChaosInSerialMode(experimentsDetails, chaosDetails, eventsDetails, clients):
    """
        injectChaosInSerialMode delete the target application pods serial mode(one by one)
    """
    #Initialising GracePeriod
    GracePeriod = 0

    #ChaosStartTimeStamp contains the start timestamp, when the chaos injection begin
    ChaosStartTimeStamp = datetime.now()
    duration = (datetime.now() - ChaosStartTimeStamp).seconds

    while duration < experimentsDetails.ChaosDuration:
        # Get the target pod details for the chaos execution
        # if the target pod is not defined it will derive the random target pod list using pod affected percentage
        if experimentsDetails.TargetPods == "" and chaosDetails.AppDetail.Label == "":
            return ValueError("Please provide one of the appLabel or TARGET_PODS")

        targetPodList, err = pods.Pods().GetPodList(
            experimentsDetails.TargetPods, experimentsDetails.PodsAffectedPerc, chaosDetails, clients)
        if err is not None:
            return err

        podNames = []
        for pod in targetPodList.items:
            podNames.append(pod.metadata.name)

        logging.info("[Info]: Target pods list, %s", podNames)

        if experimentsDetails.EngineName != "":
            msg = "Injecting " + experimentsDetails.ExperimentName + " chaos on application pod"
            types.SetEngineEventAttributes(
                eventsDetails, types.ChaosInject, msg, "Normal", chaosDetails)
            events.GenerateEvents(
                eventsDetails, chaosDetails, "ChaosEngine", clients)

        #Deleting the application pod
        for pod in targetPodList.items:

            logging.info(
                "[Info]: Killing the following pods, PodName : %s", pod.metadata.name)
            try:
                if experimentsDetails.Force:
                    clients.clientCoreV1.delete_namespaced_pod(
                        pod.metadata.name, experimentsDetails.AppNS, grace_period_seconds=GracePeriod)
                else:
                    clients.clientCoreV1.delete_namespaced_pod(
                        pod.metadata.name, experimentsDetails.AppNS)
            except Exception as exp:
                return exp

            if chaosDetails.Randomness:
                err = common.RandomInterval(experimentsDetails.ChaosInterval)
                if err is not None:
                    return err
            else:
                #Waiting for the chaos interval after chaos injection
                if experimentsDetails.ChaosInterval != "":
                    logging.info("[Wait]: Wait for the chaos interval %s",
                                 (experimentsDetails.ChaosInterval))
                    waitTime = maths.atoi(experimentsDetails.ChaosInterval)
                    common.WaitForDuration(waitTime)

            #Verify the status of pod after the chaos injection
            logging.info(
                "[Status]: Verification for the recreation of application pod")
            err = status.Application().CheckApplicationStatus(
                experimentsDetails.AppNS,experimentsDetails.AppLabel,
                experimentsDetails.Timeout, experimentsDetails.Delay, clients
            )
            if err is not None:
                return err

            duration = (datetime.now() - ChaosStartTimeStamp).seconds

    logging.info("[Completion]: %s chaos is done",
                 (experimentsDetails.ExperimentName))

    return None

def injectChaosInParallelMode(experimentsDetails, chaosDetails, eventsDetails, clients):
    """
        injectChaosInParallelMode delete the target application pods in parallel mode (all at once)
    """
    #Initialising GracePeriod
    GracePeriod = 0
    #ChaosStartTimeStamp contains the start timestamp, when the chaos injection begin
    ChaosStartTimeStamp = datetime.now()
    duration = (datetime.now() - ChaosStartTimeStamp).seconds

    while duration < experimentsDetails.ChaosDuration:
        # Get the target pod details for the chaos execution
        # if the target pod is not defined it will derive the random target pod list using pod affected percentage
        if experimentsDetails.TargetPods == "" and chaosDetails.AppDetail.Label == "":
            return ValueError("Please provide one of the appLabel or TARGET_PODS")

        targetPodList, err = pods.Pods().GetPodList(experimentsDetails.TargetPods,
                                                    experimentsDetails.PodsAffectedPerc, chaosDetails, clients)
        if err is not None:
            return err

        podNames = []
        for pod in targetPodList.items:
            podNames.append(str(pod.metadata.name))

        logging.info("[Info]: Target pods list for chaos, %s", (podNames))

        if experimentsDetails.EngineName != "":
            msg = "Injecting " + experimentsDetails.ExperimentName + " chaos on application pod"
            types.SetEngineEventAttributes(
                eventsDetails, types.ChaosInject, msg, "Normal", chaosDetails)
            events.GenerateEvents(
                eventsDetails, chaosDetails, "ChaosEngine", clients)

        #Deleting the application pod
        for pod in targetPodList.items:
            logging.info(
                "[Info]: Killing the following pods, PodName : %s", pod.metadata.name)

            try:
                if experimentsDetails.Force:
                    clients.clientCoreV1.delete_namespaced_pod(
                        pod.metadata.name, experimentsDetails.AppNS, grace_period_seconds=GracePeriod)
                else:
                    clients.clientCoreV1.delete_namespaced_pod(
                        pod.metadata.name, experimentsDetails.AppNS)
            except Exception as err:
                return err

        if chaosDetails.Randomness:
            err = common.RandomInterval(experimentsDetails.ChaosInterval)
            if err is not None:
                return err
        else:
            #Waiting for the chaos interval after chaos injection
            if experimentsDetails.ChaosInterval != "":
                logging.info("[Wait]: Wait for the chaos interval %s",
                             experimentsDetails.ChaosInterval)
                waitTime = maths.atoi(experimentsDetails.ChaosInterval)
                common.WaitForDuration(waitTime)

        #Verify the status of pod after the chaos injection
        logging.info(
            "[Status]: Verification for the recreation of application pod")
        err = status.Application().CheckApplicationStatus(
			experimentsDetails.AppNS, experimentsDetails.AppLabel,
			experimentsDetails.Timeout, experimentsDetails.Delay, clients
		)
        if err is not None:
            return err
        duration = (datetime.now() - ChaosStartTimeStamp).seconds

    logging.info("[Completion]: %s chaos is done",
                 (experimentsDetails.ExperimentName))

    return None
