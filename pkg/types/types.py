'''
    types package
'''


# PreChaosCheck initial stage of experiment check for health before chaos injection
PreChaosCheck = "PreChaosCheck"
# PostChaosCheck  pre-final stage of experiment check for health after chaos injection
PostChaosCheck = "PostChaosCheck"
# Summary final stage of experiment update the verdict
Summary = "Summary"
# ChaosInject this stage refer to the main chaos injection
ChaosInject = "ChaosInject"
# AwaitedVerdict marked the start of test
AwaitedVerdict = "Awaited"
# PassVerdict marked the verdict as passed in the end of experiment
PassVerdict = "Pass"
# FailVerdict marked the verdict as failed in the end of experiment
FailVerdict = "Fail"
# StoppedVerdict marked the verdict as stopped in the end of experiment
StoppedVerdict = "Stopped"


class ResultDetails(object):
    ''' ResultDetails is for collecting all the chaos-result-related details '''

    def __init__(self, Name=None, Verdict=None, FailStep=None, Phase=None,
                 PassedProbeCount=None, UID=None):
        self.Name = Name
        self.Verdict = Verdict
        self.FailStep = FailStep
        self.Phase = Phase
        self.ResultUID = UID
        self.PassedProbeCount = PassedProbeCount


class EventDetails(object):
    ''' EventDetails is for collecting all the events-related details '''

    def __init__(self, Message=None, Reason=None, ResourceName=None, Type=None, UID=None):
        self.Message = Message
        self.Reason = Reason
        self.ResourceName = ResourceName
        self.ResourceUID = UID
        self.Type = Type


class AppDetails(object):
    ''' AppDetails contains all the application related envs '''

    def __init__(self, Namespace=None, Label=None, Kind=None, AnnotationCheck=None, AnnotationKey=None, AnnotationValue=None):
        self.Namespace = Namespace
        self.Label = Label
        self.Kind = Kind
        self.AnnotationCheck = AnnotationCheck
        self.AnnotationKey = AnnotationKey
        self.AnnotationValue = AnnotationValue


class ChaosDetails(object):
    ''' ChaosDetails is for collecting all the global variables '''

    def __init__(self, ChaosPodName=None, ChaosNamespace=None, EngineName=None, InstanceID=None,
                 ExperimentName=None, Timeout=None, Delay=None, ChaosDuration=None, JobCleanupPolicy=None,
                 Randomness=None, Namespace=None, Label=None, Kind=None, AnnotationCheck=None,
                 AnnotationKey=None, AnnotationValue=None, UID=None
                 ):
        self.ChaosUID = UID
        self.ChaosNamespace = ChaosNamespace
        self.ChaosPodName = ChaosPodName
        self.EngineName = EngineName
        self.InstanceID = InstanceID
        self.ExperimentName = ExperimentName
        self.Timeout = Timeout
        self.Delay = Delay
        self.AppDetail = AppDetails(
            Namespace, Label, Kind, AnnotationCheck, AnnotationKey, AnnotationValue)
        self.ChaosDuration = ChaosDuration
        self.JobCleanupPolicy = JobCleanupPolicy
        self.Randomness = Randomness
        self.ParentsResources = []

    def append(self, value):
        ''' append adds resources to the parents resources '''
        self.ParentsResources.append(value)


def SetResultAttributes(ResultDetails, ChaosDetails):
    ''' SetResultAttributes initialise all the chaos result ENV '''
    ResultDetails.Verdict = "Awaited"
    ResultDetails.Phase = "Running"
    ResultDetails.FailStep = "N/A"
    ResultDetails.PassedProbeCount = 0
    if ChaosDetails.EngineName != "":
        ResultDetails.Name = ChaosDetails.EngineName + "-" + ChaosDetails.ExperimentName
    else:
        ResultDetails.Name = ChaosDetails.ExperimentName

    if ChaosDetails.InstanceID != "":
        ResultDetails.Name = ResultDetails.Name + "-" + ChaosDetails.InstanceID


def SetResultAfterCompletion(ResultDetails, verdict, phase, failStep):
    ''' SetResultAfterCompletion set all the chaos result ENV in the EOT '''
    ResultDetails.Verdict = verdict
    ResultDetails.Phase = phase
    ResultDetails.FailStep = failStep


def SetEngineEventAttributes(EventDetails, Reason, Message, Type, ChaosDetails):
    ''' SetEngineEventAttributes initialise attributes for event generation in chaos engine '''
    EventDetails.Reason = Reason
    EventDetails.Message = Message
    EventDetails.ResourceName = ChaosDetails.EngineName
    EventDetails.ResourceUID = ChaosDetails.ChaosUID
    EventDetails.Type = Type


def SetResultEventAttributes(EventDetails, Reason, Message, Type, ResultDetails):
    ''' SetResultEventAttributes initialise attributes for event generation in chaos result '''
    EventDetails.Reason = Reason
    EventDetails.Message = Message
    EventDetails.ResourceName = ResultDetails.Name
    EventDetails.ResourceUID = ResultDetails.ResultUID
    EventDetails.Type = Type
