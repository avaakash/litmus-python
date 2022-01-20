'''
    chaosresult package
'''


import os
import subprocess
from jinja2 import Environment, select_autoescape, PackageLoader

from pkg.events import events
from pkg.types import types


class ChaosResults(object):
    ''' ChaosResult Class to Create, Path and track result details '''

    def ChaosResult(self, chaosDetails, resultDetails, state, clients):
        ''' ChaosResult Create and Update the chaos result'''

        # Initialise experimentLabel
        experimentLabel = {}

        # It will list all the chaos-result with matching label
        # Note: We have added labels inside chaos result and looking for matching labels to list the chaos-result
        try:
            resultList = clients.clientDyn.resources.get(api_version="litmuschaos.io/v1alpha1", kind="ChaosResult").get(
                namespace=chaosDetails.ChaosNamespace, label_selector="name=" + resultDetails.Name)
        except Exception:
            return ValueError(
                f"Failed to get ChaosResult with matching label name={resultDetails.Name} in namespace {chaosDetails.ChaosNamespace}")

        # as the chaos pod won't be available for stopped phase
        # skipping the derivation of labels from chaos pod, if phase is stopped
        if chaosDetails.EngineName != "" and resultDetails.Phase != "Stopped":
            # Getting chaos pod label and passing it in chaos result
            try:
                chaosPod = clients.clientCoreV1.read_namespaced_pod(
                    chaosDetails.ChaosPodName, chaosDetails.ChaosNamespace)
                experimentLabel = chaosPod.metadata.labels
            except Exception as exp:
                return ValueError(f"failed to find chaos pod with name: {chaosDetails.ChaosPodName}, err: {exp}")

        experimentLabel["name"] = resultDetails.Name
        experimentLabel["chaosUID"] = str(chaosDetails.ChaosUID)

        # if there is no chaos-result with given label, it will create a new chaos-result
        if len(resultList.items) == 0:
            return self.InitializeChaosResult(chaosDetails,  resultDetails, experimentLabel)

        # the chaos-result is already present with matching labels
        # it will patch the new parameters in the same chaos-result
        if state == "SOT":
            return self.PatchChaosResult(resultList.items[0],  chaosDetails, resultDetails, experimentLabel)

        # it will patch the chaos-result in the end of experiment
        resultDetails.Phase = "Completed"

        return self.PatchChaosResult(resultList.items[0],  chaosDetails, resultDetails, experimentLabel)

    def InitializeChaosResult(self, chaosDetails, resultDetails, experimentLabel,
                              passedRuns=0,  failedRuns=0, stoppedRuns=0, probeSuccessPercentage="Awaited"):
        ''' InitializeChaosResult or patch the chaos result '''

        try:
            env_tmpl = Environment(loader=PackageLoader('pkg', 'result'), trim_blocks=True, lstrip_blocks=True,
                                   autoescape=select_autoescape(['yaml']))
            template = env_tmpl.get_template('chaos-result.j2')
            updated_chaosresult_template = template.render(
                name=resultDetails.Name, namespace=chaosDetails.ChaosNamespace, labels=experimentLabel,
                instanceId=chaosDetails.InstanceID, engineName=chaosDetails.EngineName, failStep=resultDetails.FailStep,
                experimentName=chaosDetails.ExperimentName, phase=resultDetails.Phase, verdict=resultDetails.Verdict,
                passedRuns=passedRuns,  failedRuns=failedRuns, stoppedRuns=stoppedRuns,
                probeSuccessPercentage=probeSuccessPercentage
            )

            with open('chaosresult.yaml', "w+", encoding="utf-8") as f:
                f.write(updated_chaosresult_template)

            # if the chaos result is already present, it will patch the new parameters with the existing chaos result CR
            # Note: We have added labels inside chaos result and looking for matching labels to list the chaos-result
            # these labels were not present inside earlier releases so giving a retry/update if someone have a exiting result CR
            # in his cluster, which was created earlier with older release/version of litmus.
            # it will override the params and add the labels to it so that it will work as desired.
            chaosresult_update_cmd_args_list = [
                'kubectl', 'apply', '-f', 'chaosresult.yaml', '-n', chaosDetails.ChaosNamespace]
            run_cmd = subprocess.Popen(
                chaosresult_update_cmd_args_list, stdout=subprocess.PIPE, env=os.environ.copy())
            run_cmd.communicate()
        except Exception as exp:
            return exp

        return None

    def PatchChaosResult(self, result, chaosDetails, resultDetails, chaosResultLabel):
        ''' PatchChaosResult Update the chaos result '''

        passedRuns = 0
        failedRuns = 0
        stoppedRuns = 0
        #isAllProbePassed, probeStatus = self.GetProbeStatus(resultDetails)
        if str(resultDetails.Phase).lower() == "completed":

            if str(resultDetails.Verdict).lower() == "pass":
                probeSuccessPercentage = "100"
                passedRuns = result.status.history.passedRuns + 1
            elif str(resultDetails.Verdict).lower() == "fail":
                failedRuns = result.status.history.failedRuns + 1
                probeSuccessPercentage = "0"
            elif str(resultDetails.Verdict).lower() == "stopped":
                stoppedRuns = result.status.history.stoppedRuns + 1
                probeSuccessPercentage = "0"
        else:
            probeSuccessPercentage = "Awaited"

        # It will update the existing chaos-result CR with new values
        return self.InitializeChaosResult(chaosDetails, resultDetails, chaosResultLabel,
                                          passedRuns, failedRuns, stoppedRuns, probeSuccessPercentage)

    def SetResultUID(self, resultDetails, clients):
        ''' SetResultUID sets the ResultUID into the ResultDetails structure '''

        try:
            chaosResults = clients.clientDyn.resources.get(
                api_version="litmuschaos.io/v1alpha1", kind="ChaosResult").get()
            if len(chaosResults.items) == 0:
                raise Exception("Unable to get ChaosResult")
            for result in chaosResults.items:
                if result.metadata.name == resultDetails.Name:
                    resultDetails.ResultUID = result.metadata.uid
                    return None
        except Exception as exp:
            return exp
        return None

    def RecordAfterFailure(self, chaosDetails, resultDetails, failStep, eventsDetails, clients):
        ''' RecordAfterFailure update the chaosresult and create the summary events '''

        # update the chaos result
        types.SetResultAfterCompletion(
            resultDetails, "Fail", "Completed", failStep)
        self.ChaosResult(chaosDetails,  resultDetails, "EOT", clients)

        # add the summary event in chaos result
        msg = "experiment: " + chaosDetails.ExperimentName + \
            ", Result: " + resultDetails.Verdict
        types.SetResultEventAttributes(
            eventsDetails, types.FailVerdict, msg, "Warning", resultDetails)
        events.GenerateEvents(eventsDetails,  chaosDetails,
                              "ChaosResult", clients)

        # add the summary event in chaos engine
        if chaosDetails.EngineName != "":
            types.SetEngineEventAttributes(
                eventsDetails, types.Summary, msg, "Warning", chaosDetails)
            events.GenerateEvents(
                eventsDetails,  chaosDetails, "ChaosEngine", clients)
