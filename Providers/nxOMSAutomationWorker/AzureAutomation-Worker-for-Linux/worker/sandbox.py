#!/usr/bin/env python2
#
# Copyright (C) Microsoft Corporation, All rights reserved.

"""Sandbox Class."""

import os
import sys
import time
import traceback
from Queue import Queue

import configuration
import tracer
from httpclientfactory import HttpClientFactory
from job import Job
from jrdsclient import JRDSClient
from workerexception import *

routine_loop = True
job_map = {}


def safe_loop(func):
    def decorated_func(*args, **kwargs):
        global routine_loop
        while routine_loop:
            try:
                func(*args, **kwargs)
            except SystemExit:
                tracer.log_exception_trace(traceback.format_exc())
                sys.exit(1)
            except Exception:
                tracer.log_exception_trace(traceback.format_exc())
            time.sleep(configuration.get_jrds_get_job_actions_pooling_freq())

    return decorated_func


class Sandbox:
    def __init__(self):
        self.sandbox_id = os.environ["sandbox_id"]
        tracer.log_sandbox_starting(self.sandbox_id, os.getpid())
        http_client_factory = HttpClientFactory(configuration.get_jrds_cert_path(), configuration.get_jrds_key_path())
        http_client = http_client_factory.create_http_client(sys.version_info, configuration.get_verify_certificates())
        self.jrds_client = JRDSClient(http_client)

    @staticmethod
    def stop_tracking_terminated_jobs():
        terminated_job_ids = []

        # clean up finished jobs
        for job_id, job_tuple in job_map.items():
            if job_tuple[0].isAlive() is False:
                terminated_job_ids.append(job_id)

        for job_id in terminated_job_ids:
            removal = job_map.pop(job_id, None)
            if removal is not None:
                tracer.log_debug_trace("Sandbox stopped tracking job : " + str(job_id))

    @safe_loop
    def routine(self):
        # clean up finished jobs
        self.stop_tracking_terminated_jobs()

        # get job actions
        try:
            job_actions = self.jrds_client.get_job_actions(self.sandbox_id)
        except JrdsSandboxTerminated:
            tracer.log_debug_trace("Terminating sandbox.")
            global routine_loop
            routine_loop = False
            return

        for job_action in job_actions:
            # tracer.log_informational_trace(str(job_action))

            job_id = job_action["JobId"]
            job_data = self.jrds_client.get_job_data(job_id)
            # tracer.log_informational_trace(str(job_data))

            # if there are pending action, take action, else create new job
            if job_data["pendingActionData"] is not None:
                # placeholder for action on running jobs
                tracer.log_debug_trace("Found pending action")
            else:
                job_message_queue = Queue()
                job = Job(self.sandbox_id, job_id, job_message_queue,
                          self.jrds_client)  # TODO(dalbe) : use new JRDS instance
                job_map[job_id] = (job, job_message_queue)
                job.start()


def main():
    # configuration has to be read first thing
    configuration.set_config({configuration.COMPONENT: "sandbox"})
    configuration.set_config({configuration.WORKING_DIR: os.getcwd()})
    # do not trace anything before this point

    sandbox = Sandbox()
    sandbox.routine()


if __name__ == "__main__":
    main()
