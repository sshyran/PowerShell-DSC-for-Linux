#!/usr/bin/env python
# ====================================
# Copyright (c) Microsoft Corporation. All rights reserved.
# See license.txt for license information.
# ====================================
import os
import sys


def init_locals(WorkspaceId, RegDomain):
    if WorkspaceId is None:
        WorkspaceId = ''
    if RegDomain is None:
        RegDomain = ''
    return WorkspaceId, RegDomain


def Set_Marshall(WorkspaceId, Enabled, RegDomain):
    (WorkspaceId, RegDomain) = init_locals(WorkspaceId, RegDomain)
    if (Enabled):
        i = 1
    else:
        #TODO: read the state file and try to see if the process is running, kill it if its runnning
        try:
            os.remove(worker_state_path)
        except Exception:
            pass

    return [0]


def Test_Marshall(WorkspaceId, Enabled, RegDomain):
    (WorkspaceId, RegDomain) = init_locals(WorkspaceId, RegDomain)
    if (Enabled):
        if (os.path.isfile(worker_conf_path)):
            if (os.path.isfile(worker_state_path)):
                #TODO: read the file and see if the process is running
                return [0]
    else:
        #Enabled is False
        if (not os.path.isfile(worker_conf_path)):
            if (not os.path.isfile(worker_state_path)):
                return [0]
    return [-1]


def Get_Marshall(WorkspaceId, Enabled, RegDomain):
    arg_names = list(locals().keys())
    (WorkspaceId, RegDomain) = init_locals(WorkspaceId, RegDomain)
    retval = 0
    retd = {}
    ld = locals()
    for k in arg_names:
        retd[k] = ld[k]
    return retval, retd


# ###########################################################
# Begin user defined DSC functions
# ###########################################################

worker_conf_path="/var/opt/microsoft/omsagent/state/automationworker/Worker.conf"
worker_state_path="/var/opt/microsoft/omsagent/state/automationworker/ WorkerState.conf"
