#!/usr/bin/env python2
#
# Copyright (C) Microsoft Corporation, All rights reserved.

import os
import subprocess
import sys
import threading
import time
import traceback

import configuration
import subprocessfactory
import tracer
from httpclientfactory import HttpClientFactory
from jrdsclient import JRDSClient


def safe_loop(func):
    def decorated_func(*args, **kwargs):
        while True:
            try:
                func(*args, **kwargs)
            except Exception:
                tracer.log_exception_trace(traceback.format_exc())
            time.sleep(configuration.get_jrds_get_sandbox_actions_pooling_freq())

    return decorated_func


def background_thread(func):
    def decorated_func(*args, **kwargs):
        t = threading.Thread(target=func, args=args)
        t.start()

    return decorated_func


def exit_on_error(message, exit_code=1):
    print str(message)
    open("automation_worker_crash.log", "w").write(message)
    sys.exit(exit_code)


def validate_and_setup_path():
    # default to user dir for exception logs to be writen to disk
    os.chdir(os.path.expanduser("~"))

    # test certificate and key path
    if not os.path.isfile(configuration.get_jrds_cert_path()) or not os.path.isfile(configuration.get_jrds_key_path()):
        exit_on_error("Invalid certificate of key file path (absolute path is required).")

    # test working dir
    if not os.path.exists(configuration.get_working_dir()):
        exit_on_error("Invalid working directory path (absolute path is required).")
    else:
        os.chdir(configuration.get_working_dir())

    # test write access to working dir
    try:
        test_file_name = "test_file"
        open(test_file_name, "a").write(test_file_name)
        os.remove(test_file_name)
    except IOError:
        exit_on_error("Invalid working directory permission (read/write permissions are required).")


class Worker:
    def __init__(self):
        tracer.log_worker_starting(configuration.get_worker_version())
        http_client_factory = HttpClientFactory(configuration.get_jrds_cert_path(), configuration.get_jrds_key_path())
        http_client = http_client_factory.create_http_client(sys.version_info, configuration.get_verify_certificates())
        self.jrds_client = JRDSClient(http_client)
        self.running_sandboxes = {}

    @safe_loop
    def routine(self):
        self.stop_tracking_terminated_sandbox()

        sandbox_actions = self.jrds_client.get_sandbox_actions()
        tracer.log_debug_trace("Get sandbox action. Found " + str(len(sandbox_actions)) + " action(s).")

        for action in sandbox_actions:
            tracer.log_worker_sandbox_action_found(len(sandbox_actions))
            sandbox_id = str(action["SandboxId"])

            # prevent duplicate sandbox from running
            if sandbox_id in self.running_sandboxes:
                return

            # create sandboxes folder if needed
            sandboxes_base_path = "sandboxes"
            sandbox_working_dir = os.path.join(configuration.get_working_dir(), sandboxes_base_path, sandbox_id)

            if not os.path.exists(sandbox_working_dir):
                tracer.log_debug_trace("Sandbox folder not existing.")
                try:
                    os.makedirs(sandbox_working_dir)
                except OSError:
                    tracer.log_debug_trace("Failed to create sandbox folder.")
                    pass

            cmd = ["python", os.path.join(configuration.get_sourcecode_path(), "sandbox.py")]
            process_env_variables = {"sandbox_id": sandbox_id}
            sandbox_process = subprocessfactory.create_subprocess(cmd=cmd,
                                                                  env=process_env_variables,
                                                                  stdout=subprocess.PIPE,
                                                                  stderr=subprocess.PIPE,
                                                                  cwd=sandbox_working_dir)
            self.running_sandboxes[sandbox_id] = sandbox_process
            self.monitor_sandbox_process_outputs(sandbox_id, sandbox_process)
            tracer.log_worker_starting_sandbox(sandbox_id, str(sandbox_process.pid))

    @background_thread
    def monitor_sandbox_process_outputs(self, sandbox_id, process):
        while process.poll() is None:
            output = process.stdout.readline().replace("\n", "")
            if output == '':
                continue
            if output != '':
                tracer.log_sandbox_stdout(output)

        if process.poll() != 0:
            full_error_output = ""
            while True:
                error_output = process.stderr.readline()
                if error_output is None or error_output == '':
                    break
                full_error_output += error_output
            tracer.log_debug_trace("Sandbox crashed : " + str(full_error_output))

        tracer.log_worker_sandbox_process_exited(sandbox_id, str(process.pid), process.poll())

    def stop_tracking_terminated_sandbox(self):
        terminated_sandbox_ids = []

        # detect terminated sandboxes
        for sandbox_id, sandbox_process in self.running_sandboxes.items():
            if sandbox_process.poll() is not None:
                terminated_sandbox_ids.append(sandbox_id)

        # clean-up terminated sandboxes
        for sandbox_id in terminated_sandbox_ids:
            removal = self.running_sandboxes.pop(sandbox_id, None)
            if removal is not None:
                tracer.log_debug_trace("Worker stopped tracking sandbox : " + str(sandbox_id))


def main():
    if len(sys.argv) < 2:
        exit_on_error("Invalid configuration file path (absolute path is required).")
    else:
        configuration_path = sys.argv[1]

    if not os.path.isfile(configuration_path):
        exit_on_error("Invalid configuration file path (absolute path is required).")

    # configuration has to be read first thing
    try:
        # remove the test_mode env_var value (mainly for Windows)
        # this value is set in test
        del os.environ["test_mode"]
    except KeyError:
        pass
    worker_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(worker_dir, configuration_path)
    configuration.read_and_set_configuration(config_path)
    configuration.set_config({configuration.COMPONENT: "worker"})
    validate_and_setup_path()
    # do not trace anything before this point

    worker = Worker()
    worker.routine()


if __name__ == "__main__":
    main()
