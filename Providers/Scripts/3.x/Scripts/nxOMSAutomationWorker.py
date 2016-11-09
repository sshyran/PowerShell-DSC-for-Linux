#!/usr/bin/env python
# ====================================
# Copyright (c) Microsoft Corporation. All rights reserved.
# See license.txt for license information.
# ====================================
import os
import sys
import configparser
import subprocess
import signal
import imp

nxDSCLog = imp.load_source('nxDSCLog', '../nxDSCLog.py')
omsMetaConfigHelper = imp.load_source('OMS_MetaConfigHelper', '../OMS_MetaConfigHelper.py')
LG = nxDSCLog.DSCLog

def init_locals(WorkspaceId, AzureDnsAgentSvcZone):
    if WorkspaceId is None:
        WorkspaceId = ''
    if AzureDnsAgentSvcZone is None:
        AzureDnsAgentSvcZone = ''
    return WorkspaceId, AzureDnsAgentSvcZone


def Set_Marshall(WorkspaceId, Enabled, AzureDnsAgentSvcZone):
    (WorkspaceId, AzureDnsAgentSvcZone) = init_locals(WorkspaceId, AzureDnsAgentSvcZone)
    if (Enabled):
        #call the registration script
        try:
            agent_id = read_oms_config_file()
            sp = subprocess.call(
                ["python", REGISTRATION_FILE_PATH, "--register", "-w " + WorkspaceId, "-a " + agent_id,
                 "-c " + OMS_CERTIFICATE_PATH, "-k " + OMS_CERT_KEY_PATH, "-p " + WORKING_DIRECTORY_PATH])
            if sp != 0:
                LG().Log('ERROR', "Linux Hybrid Worker registration failed")
                return [-1]
            if not os.path.isfile(WORKER_CONF_PATH):
                LG().Log('ERROR', "Linux Hybrid Worker registration file could not be created")
                return [-1]
        except Exception as exception:
            LG().Log('ERROR', exception.message)

        # Read the worker state file and try to kill linux hybrid worker process if running
        try:
            (pid, workspace_id) = read_worker_state()
        except Exception as exception:
            LG().Log('ERROR', exception.message)
        try:
            command = subprocess.check_output(["ps", "-p", str(pid), "-o", "comm="])
        except subprocess.CalledProcessError:
            pass
        except Exception as exception:
            LG().Log('ERROR', exception.message)
            return [-1]
        else:
            # Kill the worker if it matches the description
            if command.__contains__(WorkspaceId):
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    LG().Log('ERROR', "Could not kill Linux Hybrid Worker process")
                    return [-1]
        # Start the worker script
        try:
            sp = subprocess.call(
                ["python", HYBRID_WORKER_START_PATH, "-c " + WORKER_CONF_PATH, "-w " + workspace_id])
            if sp != 0:
                LG().Log('ERROR', "Could not start Linux Hybrid Worker process")
                return [-1]
        except Exception as exception:
            LG().Log('ERROR', exception)
            return [-1]
    else:
        try:
            (pid, workspace_id) = read_worker_state()
            command = subprocess.check_output(["ps", "-p", str(pid), "-o", "comm="])
        except configparser.Error:
            # if config parser error occurs file probably does't exist
            pass
        except subprocess.CalledProcessError:
            # the config file was read, but the process is not running
            # delete the config file only
            try:
                os.remove(WORKER_STATE_PATH)
            except Exception as exception:
                LG().Log('ERROR', "Could not delete file " + WORKER_STATE_PATH + exception.message)
                return [-1]
        else:
            # the state file was properly read and the worker PID exists
            try:
                os.kill(pid, signal.SIGTERM)
                os.remove(WORKER_STATE_PATH)
            except Exception as exception:
                LG().Log('ERROR', exception.message)
                return [-1]
        try:
             os.remove(WORKER_CONF_PATH)
        except Exception as exception:
            LG().Log('ERROR', "Could not delete file " + WORKER_STATE_PATH + exception.message)
            return [-1]
    return [0]


def Test_Marshall(WorkspaceId, Enabled, AzureDnsAgentSvcZone):
    (WorkspaceId, AzureDnsAgentSvcZone) = init_locals(WorkspaceId, AzureDnsAgentSvcZone)
    if Enabled:
        if os.path.isfile(WORKER_CONF_PATH):
            # read the version number and compare
            config = configparser.ConfigParser()
            config.read(WORKER_STATE_PATH)
            try:
                registered_version = read_worker_registration_conf()
                version_file = open(MODULE_VERSION_FILE, "r")
            except Exception as exception:
                LG().Log('INFO', exception.message)
                return [-1]
            current_version = version_file.read().strip()
            if not registered_version.__eq__(current_version):
                LG().Log('INFO', "The installed and available versions of nxOMSAutomationWorker did not match")
                return [-1]
            if os.path.isfile(WORKER_STATE_PATH):
                try:
                    (pid, workspace_id) = read_worker_state()
                    command = subprocess.check_output(["ps","-p", str(pid), "-o", "comm="])
                except Exception:
                    LG().Log('INFO', "The process for Linux Hybrid Worker is not running")
                    return [-1]
                if not command.__contains__(workspace_id):
                    LG().Log('INFO', "Could not find the process for Linux Hybrid Worker")
                    return [-1]
                return [0]
    else:
        #Enabled is False
        if not os.path.isfile(WORKER_CONF_PATH):
            if not os.path.isfile(WORKER_STATE_PATH):
                return [0]
    return [-1]


def Get_Marshall(WorkspaceId, Enabled, AzureDnsAgentSvcZone):
    arg_names = list(locals().keys())
    (WorkspaceId, AzureDnsAgentSvcZone) = init_locals(WorkspaceId, AzureDnsAgentSvcZone)
    retval = 0
    retd = {}
    ld = locals()
    for k in arg_names:
        retd[k] = ld[k]
    return retval, retd


# ###########################################################
# Begin user defined DSC functions
# ###########################################################

STATE_SECTION="[worker-state]" # This value is a placeholder
PID="PID"
WORKSPACE_ID="workspaceId"
CONFIGURATION="[configuration]"
DSC_RESROUCE_VERSION="dsc_resource_version"
AGENT_ID="AGENT_GUID"

WORKER_CONF_PATH= "/var/opt/microsoft/omsagent/state/automationworker/Worker.conf"
WORKER_STATE_PATH= "/var/opt/microsoft/omsagent/state/automationworker/ WorkerState.conf"
MODULE_VERSION_FILE= "/opt/microsoft/omsconfig/modules/nxOMSAutomationWorker/VERSION"
OMS_ADMIN_CONFIG_FILE="/etc/opt/microsoft/omsagent/conf/omsadmin.conf"
OMS_CERTIFICATE_PATH="/etc/opt/microsoft/omsagent/certs/oms.crt"
OMS_CERT_KEY_PATH= "/etc/opt/microsoft/omsagent/certs/oms.key"
WORKING_DIRECTORY_PATH="/var/opt/microsoft/omsagent/tmp/"
REGISTRATION_FILE_PATH="/opt/microsoft/omsconfig/modules/nxOMSAutomationWorker/DSCResources/MSFT_nxOMSAutomationWorkerResource/automationworker/scripts/register_oms.py"
HYBRID_WORKER_START_PATH="/opt/microsoft/omsconfig/modules/nxOMSAutomationWorker/DSCResources/MSFT_nxOMSAutomationWorkerResource/automationworker/scripts/worker/main.py"

def read_worker_state():
    if os.path.isfile(WORKER_STATE_PATH):
        state = configparser.ConfigParser()
        try:
            state.read(WORKER_STATE_PATH)
            pid = state.get(STATE_SECTION, PID)
            workspace_id = state.get(STATE_SECTION, WORKSPACE_ID)
        except configparser.NoSectionError as exception:
            LG().Log('DEBUG', exception.message)
            raise exception
        except configparser.NoOptionError as exception:
            LG().Log('DEBUG', exception.message)
            raise exception
        return pid, workspace_id
    else:
        error_string = "could not find file" + WORKER_STATE_PATH
        LG().Log('DEUBG', error_string)
        raise ValueError(error_string);

def read_worker_registration_conf():
    if os.path.isfile(WORKER_CONF_PATH):
        conf = configparser.ConfigParser()
        try:
            conf.read(WORKER_CONF_PATH)
            dsc_resoruce_version = conf.get(CONFIGURATION, DSC_RESROUCE_VERSION)
        except configparser.NoSectionError as exception:
            LG().Log('DEBUG', exception.message)
            raise exception
        except configparser.NoOptionError as exception:
            LG().Log('DEUBG', exception.message)
            raise exception
        return dsc_resoruce_version
    else:
        error_string = "could not find file" + WORKER_CONF_PATH
        LG().Log('DEUBG', error_string)
        raise ValueError(error_string);

def read_oms_config_file():
    if os.path.isfile(OMS_ADMIN_CONFIG_FILE):
        try:
            keyvals = omsMetaConfigHelper.source_file(OMS_ADMIN_CONFIG_FILE)
            return keyvals[AGENT_ID].strip()
        except configparser.NoSectionError as exception:
            LG().Log('DEBUG', exception.message)
            raise exception
        except configparser.NoOptionError as exception:
            LG().Log('DEUBG', exception.message)
            raise exception
    else:
        error_string = "could not find file" + OMS_ADMIN_CONFIG_FILE
        LG().Log('DEUBG', error_string)
        raise ValueError(error_string);
