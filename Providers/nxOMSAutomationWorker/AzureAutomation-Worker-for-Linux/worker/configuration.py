#!/usr/bin/env python2
#
# Copyright (C) Microsoft Corporation, All rights reserved.

import ConfigParser
import os
import sys

import serializerfactory

CONFIG_ENV_KEY = "WORKERCONF"
CONFIG_SECTION = "configuration"

COMPONENT = "component"
CERT_PATH = "jrds_cert_path"
KEY_PATH = "jrds_key_path"
BASE_URI = "jrds_base_uri"
ACCOUNT_ID = "account_id"
MACHINE_ID = "machine_id"
HYBRID_WORKER_GROUP_NAME = "hybrid_worker_group_name"
WORKER_VERSION = "worker_version"
WORKING_DIR = "working_dir"
DEBUG_TRACES = "debug_traces"
BYPASS_CERTIFICATE_VERIFICATION = "bypass_certificate_verification"
SOURCECODE_PATH = "sourcecode_path"

json = serializerfactory.get_serializer(sys.version_info)


def read_and_set_configuration(config_path):
    """Reads the worker configuration from the file at config_path and sets the read configuration to
    the env variable.

    The configuration is read of the path, put into a dictionary which will be serialized and set in the env
    variable.

    Notes:
        The WORKER_VERSION has to be set manually for now.
        The COMPONENT has to be set manually at the entry point of each component (worker/sandbox).

    Args:
        config_path: string, the configuration file path.
    """
    try:
        del os.environ[CONFIG_ENV_KEY]
    except Exception:
        pass

    config = ConfigParser.ConfigParser()
    config.read(config_path)

    configuration = {CERT_PATH: os.path.abspath(config.get(CONFIG_SECTION, CERT_PATH)),
                     KEY_PATH: os.path.abspath(config.get(CONFIG_SECTION, KEY_PATH)),
                     BASE_URI: config.get(CONFIG_SECTION, BASE_URI),
                     ACCOUNT_ID: config.get(CONFIG_SECTION, ACCOUNT_ID),
                     MACHINE_ID: config.get(CONFIG_SECTION, MACHINE_ID),
                     HYBRID_WORKER_GROUP_NAME: config.get(CONFIG_SECTION, HYBRID_WORKER_GROUP_NAME),
                     WORKING_DIR: os.path.abspath(config.get(CONFIG_SECTION, WORKING_DIR)),
                     DEBUG_TRACES: config.getboolean(CONFIG_SECTION, DEBUG_TRACES),
                     BYPASS_CERTIFICATE_VERIFICATION: config.getboolean(CONFIG_SECTION,
                                                                        BYPASS_CERTIFICATE_VERIFICATION),
                     SOURCECODE_PATH: os.path.dirname(os.path.realpath(__file__)),
                     WORKER_VERSION: "8.0.0.0",  # TODO(dalbe): take version from config
                     COMPONENT: "Unknown"}
    set_config(configuration)


def set_config(configuration):
    """Sets the worker configuration to the env variable.

    This method will merge the provided dictionary to any existent value in the environment variable.

    Args:
        configuration: dictionary(string), the configuration key value pairs.
    """
    try:
        env_config = os.environ[CONFIG_ENV_KEY]
        config = json.loads(env_config)
        config.update(configuration)
        configuration = config
    except KeyError:
        pass

    os.environ[CONFIG_ENV_KEY] = json.dumps(configuration)


def get_value(key):
    """Gets a specific value from the configuration value in the environment variable.

    This method will merge the provided dictionary to any existent value in the environment variable.

    Args:
        key: string, the configuration key value.

    Returns:
        The configuration value.
    """
    try:
        return json.loads(os.environ[CONFIG_ENV_KEY])[key]
    except KeyError:
        raise KeyError("Configuration environment variable not found. [key=" + key + "].")


def get_jrds_get_sandbox_actions_pooling_freq():
    if get_value(BYPASS_CERTIFICATE_VERIFICATION):
        return 5
    else:
        return 30


def get_jrds_get_job_actions_pooling_freq():
    if get_value(BYPASS_CERTIFICATE_VERIFICATION):
        return 5
    else:
        return 30


def get_component():
    return get_value(COMPONENT)


def get_jrds_cert_path():
    return get_value(CERT_PATH)


def get_jrds_key_path():
    return get_value(KEY_PATH)


def get_jrds_base_uri():
    return get_value(BASE_URI)


def get_account_id():
    return get_value(ACCOUNT_ID)


def get_machine_id():
    return get_value(MACHINE_ID)


def get_hybrid_worker_name():
    return get_value(HYBRID_WORKER_GROUP_NAME)


def get_worker_version():
    return get_value(WORKER_VERSION)


def get_working_dir():
    return get_value(WORKING_DIR)


def get_debug_traces():
    return get_value(DEBUG_TRACES)


def get_verify_certificates():
    return get_value(BYPASS_CERTIFICATE_VERIFICATION)


def get_sourcecode_path():
    return get_value(SOURCECODE_PATH)
