#!/usr/bin/env python2
#
# Copyright (C) Microsoft Corporation, All rights reserved.

"""Runtime module. Contains runtime base class and language specific runtime classes."""

import os
import subprocess
from distutils.spawn import find_executable

import configuration
import subprocessfactory


class Runtime:
    """Runtime base class."""

    def __init__(self, job_data, runbook_data):
        # should be overwritten by language runtime
        self.file_extension = None
        self.execution_alias = None
        self.base_cmd = None

        # used for actual runtime
        self.runbook_file_path = None
        self.runbook_subprocess = None
        self.runbook_data = runbook_data
        self.job_data = job_data

    def start_runbook_subprocess(self):
        """Creates the runbook subprocess based on the script language and using properties set by the derived class.

        Requires self.base_cmd & self.runbook_file_path to be set by derived class.
        """
        cmd = self.base_cmd + [self.runbook_file_path]
        env = os.environ.copy()
        env["AUTOMATION_JOB_ID"] = str(self.job_data["jobId"])  # TODO (dalbe) : review key name

        # TODO(dalbe): Apply only for Python
        env["PYTHONPATH"] = str(configuration.get_sourcecode_path())  # windows env have to be str (not unicode)
        self.runbook_subprocess = subprocessfactory.create_subprocess(cmd=cmd,
                                                                      env=env,
                                                                      stdout=subprocess.PIPE,
                                                                      stderr=subprocess.PIPE)

    def write_runbook_to_disk(self):
        """Writes the runbook to disk.

        File name format : [runbookname][versionId].[extension]

        Requires self.runbook & self.file_extension to be set by derived class.
        """
        file_name = self.runbook_data["name"] + self.runbook_data["runbookVersionId"] + self.file_extension
        self.runbook_file_path = os.path.join(configuration.get_working_dir(), file_name)

        runbook_file = open(self.runbook_file_path, 'w+')
        runbook_file.write(self.runbook_data["definition"].encode("utf-8"))
        runbook_file.close()

    def is_runtime_supported(self):
        """Validates that the OS supports the language runtime by testing the executable file path.

        Returns:
            True    : If executable exist.
            False   : Otherwise.
        """
        if find_executable(self.execution_alias) is None:
            return False
        else:
            return True


class PowerShellRuntime(Runtime):
    """PowerShell runtime derived class."""

    def __init__(self, job_data, runbook_data):
        Runtime.__init__(self, job_data, runbook_data)
        self.file_extension = ".ps1"
        self.execution_alias = "powershell"
        self.base_cmd = [self.execution_alias, "-File"]


class Python2Runtime(Runtime):
    """Python 2 runtime derived class."""

    def __init__(self, job_data, runbook_data):
        Runtime.__init__(self, job_data, runbook_data)
        self.file_extension = ".py"
        self.execution_alias = "python2"

        # to allow testing on windows
        if os.name.lower() == "nt":
            self.execution_alias = "python"

        self.base_cmd = [self.execution_alias]


class Python3Runtime(Runtime):
    """Python 3 runtime derived class."""

    def __init__(self, job_data, runbook_data):
        Runtime.__init__(self, job_data, runbook_data)
        self.file_extension = ".py"
        self.execution_alias = "python3"

        # to allow testing on windows
        if os.name.lower() == "nt":
            self.execution_alias = "python"

        self.base_cmd = [self.execution_alias]


class BashRuntime(Runtime):
    """Bash runtime derived class."""

    def __init__(self, job_data, runbook_data):
        Runtime.__init__(self, job_data, runbook_data)
        self.file_extension = ".sh"
        self.execution_alias = "bash"

        self.base_cmd = [self.execution_alias]
