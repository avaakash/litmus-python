'''
    clients package
'''


import os
from kubernetes import client, config, dynamic
from kubernetes.client import api_client


class K8sClient(object):
    ''' Client Class is maintaining clients for k8s '''

    def __init__(self, conf=None):
        self.clientCoreV1 = client.CoreV1Api(conf)
        self.clientDyn = dynamic.DynamicClient(
            api_client.ApiClient(configuration=conf))
        self.clientApps = client.AppsV1Api(conf)


class Configuration(object):
    ''' Config maintain configuration for in and out cluster '''

    def __init__(self, kubeconfig=None, configurations=None):
        self.kubeconfig = kubeconfig
        self.configurations = configurations

    def get_config(self):
        ''' get_config return the configuration '''

        global configs
        if self.kubeconfig != "":
            configs = self.kubeconfig
        elif os.getenv('KUBERNETES_SERVICE_HOST'):
            configs = config.load_incluster_config()
        else:
            configs = config.load_kube_config()

        self.configurations = configs
        return configs
