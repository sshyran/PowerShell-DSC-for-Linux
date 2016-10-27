#!/usr/bin/env python
# ====================================
# Copyright (c) Microsoft Corporation. All rights reserved.
# See license.txt for license information.
# ====================================
import os
import sys


def init_locals(Name):
    if Name is None:
        Name = ''
    return Name.encode('ascii', 'ignore')


def Set_Marshall(Name, AutoRegister):
    Name = init_locals(Name)
    return [0]


def Test_Marshall(Name, AutoRegister):
    Name = init_locals(Name)
    return [0]


def Get_Marshall(Name, AutoRegister):
    arg_names = list(locals().keys())
    Name = init_locals(Name)
    retval = 0
    retd = {}
    ld = locals()
    for k in arg_names:
        retd[k] = ld[k]
    return retval, retd


# ###########################################################
# Begin user defined DSC functions
# ###########################################################

