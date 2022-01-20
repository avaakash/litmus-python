'''
    common package
'''


import time
import threading
import random
import logging
import os
import sys
import signal
import string

from pkg.types import types
from pkg.events import events
from pkg.result import chaosresult
from pkg.maths import maths


def WaitForDuration(duration):
    ''' WaitForDuration waits for the given time duration (in seconds) '''
    time.sleep(duration)


def RandomInterval(interval):
    ''' RandomInterval wait for the random interval lies between lower & upper bounds '''
    intervals = interval.split("-")
    lowerBound = 0
    upperBound = 0

    if len(intervals) == 1:
        lowerBound = 0
        upperBound = maths.atoi(intervals[0])
    elif len(intervals) == 2:
        lowerBound = maths.atoi(intervals[0])
        upperBound = maths.atoi(intervals[1])
    else:
        return logging.info("unable to parse CHAOS_INTERVAL, provide in valid format")

    waitTime = lowerBound + random.randint(0, upperBound-lowerBound)
    logging.info("[Wait]: Wait for the random chaos interval %s", (waitTime))
    WaitForDuration(waitTime)
    return None


def GetTargetContainer(appNamespace, appName, clients):
    '''
        GetTargetContainer will fetch the container name from application pod
        This container will be used as target container
    '''

    try:
        pod = clients.clientCoreV1.read_namespaced_pod(
            name=appName, namespace=appNamespace)
    except Exception as e:
        return "", e

    return pod.spec.containers[0].name, None


def GetRunID():
    ''' GetRunID generate a random '''
    runId = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=6))
    return str(runId)


def Notify(expname, resultDetails, chaosDetails, eventsDetails, clients):
    '''
        Notify Catch and relay certain signal(s) to sendor. Waiting until the abort signal recieved
    '''

    # initialising result object
    result = chaosresult.ChaosResults()
    logging.info(
        "[Chaos]: Chaos Experiment Abortion started because of terminated signal received")

    # updating the chaosresult after stopped
    failStep = "Chaos injection stopped!"
    types.SetResultAfterCompletion(
        resultDetails, "Stopped", "Stopped", failStep)

    # updating the chaosresult after stopped
    # generating summary event in chaosengine
    msg = expname + " experiment has been aborted"
    types.SetEngineEventAttributes(
        eventsDetails, types.Summary, msg, "Warning", chaosDetails)
    events.GenerateEvents(eventsDetails, chaosDetails, "ChaosEngine", clients)

    # generating summary event in chaosresult
    types.SetResultEventAttributes(
        eventsDetails, types.Summary, msg, "Warning", resultDetails)
    events.GenerateEvents(eventsDetails, chaosDetails, "ChaosResult", clients)


def AbortWatcher(expname, resultDetails, chaosDetails, eventsDetails, clients):
    '''
        AbortWatcher continuosly watch for the abort signals
        it will update chaosresult w/ failed step and create an abort event,
        if it recieved abort signal during chaos
    '''

    # sendor thread is used to transmit signal notifications.
    sender = threading.Thread(target=Notify, args=(
        expname, resultDetails, chaosDetails, eventsDetails, clients))

    def signal_handler(sig, frame):
        sender.start()
        sender.join()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


def GetIterations(duration, interval):
    ''' GetIterations derive the iterations value from given parameters '''
    iterations = 0
    if interval != 0:
        iterations = duration / interval
    return max(iterations, 1)


def Getenv(key, defaultValue):
    ''' Getenv fetch the env and set the default value, if any '''
    value = os.Getenv(key)
    if value == "":
        value = defaultValue

    return value


def FilterBasedOnPercentage(percentage, array):
    ''' FilterBasedOnPercentage return the slice of list based on the the provided percentage '''

    finalList = []
    newInstanceListLength = max(1, maths.Adjustment(percentage, len(array)))

    # it will generate the random instanceList
    # it starts from the random index and choose requirement no of volumeID next to that index in a circular way.
    index = random.randint(0, len(array))
    for _ in range(newInstanceListLength):
        finalList = finalList.append(array[index])
        index = (index + 1) % len(array)

    return finalList
