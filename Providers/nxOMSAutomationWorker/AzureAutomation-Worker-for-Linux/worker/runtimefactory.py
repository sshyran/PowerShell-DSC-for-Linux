#!/usr/bin/env python2
#
# Copyright (C) Microsoft Corporation, All rights reserved.

"""Runtime factory."""

from runtime import *
from workerexception import *

# This has to map with JRDS : RunbookDefinitionKind enum
PowerShell = 5
PYTHON2 = 9
PYTHON3 = 10
BASH = 11


def create_runtime(job_data, runbook_data):
    """Create a new instance of the appropriate language Runtime.

    Args:
        runbook_definition_kind : int, the runbook definition kind.

    Returns:
        An instance of Python2Runtime if the runbook_definition_kind parameter is "Python2".
        An instance of Python3Runtime if the runbook_definition_kind parameter is "Python3".
        An instance of BashRuntime if the runbook_definition_kind parameter is "BASH".

    Throws:
        UnsupportedRunbookType : If the OS or the worker doesn't support the specified runbook_definition_kind.
    """
    runbook_definition_kind = runbook_data["runbookDefinitionKind"]

    if runbook_definition_kind == PowerShell:
        runtime = PowerShellRuntime(job_data, runbook_data)
    elif runbook_definition_kind == PYTHON2:
        runtime = Python2Runtime(job_data, runbook_data)
    elif runbook_definition_kind == PYTHON3:
        runtime = Python3Runtime(job_data, runbook_data)
    elif runbook_definition_kind == BASH:
        runtime = BashRuntime(job_data, runbook_data)
    else:
        raise WorkerUnsupportedRunbookType()

    if runtime.is_runtime_supported() is False:
        raise OSUnsupportedRunbookType()

    return runtime
