#!/usr/bin/env python
# ====================================
# Copyright (c) Microsoft Corporation. All rights reserved.
# See license.txt for license information.
# ====================================
import os
import sys


def init_locals(Name, WorkspaceId):
    if Name is None:
        Name = ''
    if WorkspaceId is None:
        WorkspaceId = ''
    return Name.encode('ascii', 'ignore'), WorkspaceId.encode('ascii', 'ignore')


def Set_Marshall(Name, AutoRegister, WorkspaceId):
    (Name, WorkspaceId) = init_locals(Name, WorkspaceId)
    return [0]


def Test_Marshall(Name, AutoRegister, WorkspaceId):
    (Name, WorkspaceId) = init_locals(Name)
    return [0]


def Get_Marshall(Name, AutoRegister, WorkspaceId):
    arg_names = list(locals().keys())
    (Name, WorkspaceId) = init_locals(Name)
    retval = 0
    retd = {}
    ld = locals()
    for k in arg_names:
        retd[k] = ld[k]
    return retval, retd


# ###########################################################
# Begin user defined DSC functions
# ###########################################################

