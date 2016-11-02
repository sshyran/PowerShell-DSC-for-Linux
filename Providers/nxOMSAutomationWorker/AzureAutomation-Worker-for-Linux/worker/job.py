#!/usr/bin/env python2
#
# Copyright (C) Microsoft Corporation, All rights reserved.

"""Job class. This class is a representation of an "automation" job."""

import sys
import time
import traceback
from datetime import datetime
from threading import Thread

import runtimefactory
import tracer
from streamhandler import StreamHandler
from workerexception import *


class Job(Thread):
    """Job class."""

    def __init__(self, sandbox_id, job_id, msg_thread, jrds_client):
        Thread.__init__(self)
        self.sandbox_id = sandbox_id
        self.job_id = job_id
        self.msg_thread = msg_thread
        self.jrds_client = jrds_client

        # values populated in load_job()
        self.runtime = None
        self.job_data = None
        self.job_updatable_data = None
        self.runbook_data = None

    def load_job(self):
        """Load all required artifact for the job to be executed."""
        self.jrds_client.set_job_status(self.sandbox_id, self.job_id, "Activating", False)
        self.job_data = self.jrds_client.get_job_data(self.job_id)
        self.job_updatable_data = self.jrds_client.get_job_updatable_data(self.job_id)
        self.runbook_data = self.jrds_client.get_runbook_data(self.job_data["runbookVersionId"])

    def initialize_runtime(self):
        """Initializes the runtime component for the job. The runtime component is language specific."""
        self.runtime = runtimefactory.create_runtime(self.job_data, self.runbook_data)
        self.runtime.write_runbook_to_disk()

    def run(self):
        """Main job execution logic. This methods returns when the job execution is completed.

        Throws:
            WorkerUnsupportedRunbookType  : If the language isn't supported by by the worker.
            WorkerUnsupportedRunbookType  : If the language isn't supported by by the worker.
            Exception                     : Any unhandled exception.
        """
        try:
            self.load_job()
            self.initialize_runtime()
            self.execute_runbook()
            self.unload_job()
        except (WorkerUnsupportedRunbookType, OSUnsupportedRunbookType), e:
            tracer.log_debug_trace("Runbook type not supported.")
            self.jrds_client.set_job_status(self.sandbox_id, self.job_id, "Failed", True, exception=e.message)
            self.unload_job()
        except Exception:
            tracer.log_debug_trace("Job runtime exception, crashing sandbox...")
            tracer.log_exception_trace(traceback.format_exc())
            sys.exit(1)
            # TODO(dalbe) : Kill sandbox here

    def execute_runbook(self):
        """Executes the job runtime and performs runtime operation (stream upload / status change)."""
        # set status to running
        tracer.log_debug_trace("Starting runbook.")
        self.jrds_client.set_job_status(self.sandbox_id, self.job_id, "Running", False)

        # create runbook subprocess
        self.runtime.start_runbook_subprocess()

        # monitor runbook output for streams
        stream_handler = StreamHandler(self.job_data, self.runtime.runbook_subprocess,
                                       self.jrds_client)  # use new JRDS instance
        stream_handler.start()

        # wait for runbook execution to complete
        while stream_handler.isAlive() or self.runtime.runbook_subprocess.poll() is None:
            time.sleep(0.2)

        # handle terminal state changes
        if self.runtime.runbook_subprocess.poll() != 0:
            full_error_output = ""
            while True:
                error_output = self.runtime.runbook_subprocess.stderr.readline()
                if error_output is None or error_output == '':
                    break
                full_error_output = "\n".join([full_error_output, error_output])
            self.jrds_client.set_job_status(self.sandbox_id, self.job_id, "Failed", True, exception=full_error_output)
            tracer.log_debug_trace("Completed with error")
        else:
            self.jrds_client.set_job_status(self.sandbox_id, self.job_id, "Completed", True)
            tracer.log_debug_trace("Completed without error")

    def unload_job(self):
        """Unloads the job."""
        self.jrds_client.unload_job(self.sandbox_id, self.job_id, self.job_updatable_data["isDraft"], datetime.now(), 2)
        tracer.log_debug_trace("Unloading job.")
