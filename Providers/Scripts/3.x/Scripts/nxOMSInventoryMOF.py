#!/usr/bin/env python
#============================================================================
# Copyright (C) Microsoft Corporation, All rights reserved. 
#============================================================================

import os
import imp
import re
import codecs
import shutil
import string

protocol = imp.load_source('protocol', '../protocol.py')
nxDSCLog = imp.load_source('nxDSCLog', '../nxDSCLog.py')

LG = nxDSCLog.DSCLog

inventoryMof_path = '/etc/opt/microsoft/omsagent/conf/omsagent.d/inventory.mof'

def init_vars(Instances):
    new_instances = []
    if Instances is not None :
        for instance in Instances:
            if instance['InstanceName'].value is not None:
                instance['InstanceName']=instance['InstanceName'].value

            if instance['ClassName'].value is not None:
                instance['ClassName']=instance['ClassName'].value

            new_properties = []
            if instance['Properties'] is not None and len(customlog['Properties'].value) > 0:
                for property in instance['Properties'].value:
                    if property is not None and len(property) > 0:
                        new_properties.append(property)

            if len(new_properties) > 0:
                instance['Properties'] = new_properties
                new_instances.append(instance)

    Instances = new_instances
    
def Set_Marshall(FilePath, Ensure = False, Instances = None):
    init_vars(Instances)
    Set(Ensure, Instances)
    return [0]

def Test_Marshall(FilePath, Ensure = False, Instances = None):
    init_vars(Instances)
    return Test(Ensure, Instances)

def Get_Marshall(Properties, Ensure = False, Instances = None):
    arg_names = list(locals().keys())
    init_vars(Instances)
    
    CurrentInstances = Instances
    Name = protocol.MI_String(Name)
    Ensure = protocol.MI_Boolean(Ensure)
    for instance in CurrentInstances:
        instance['InstanceName'] = protocol.MI_String(instance['InstanceName'])
        instance['ClassName'] = protocol.MI_String(instance['ClassName'])
        if instance['Properties'] is not None and len(instance['Properties']):
            instance['Properties'] = protocol.MI_StringA(instance['Properties'])
    Instances = protocol.MI_InstanceA(CurrentInstances)
    retd = {}
    ld = locals()
    for k in arg_names:
        retd[k] = ld[k]
    return 0, retd
            
def Set(Ensure, Instances):
    GenerateInventoyMOF(Instances)
    return [0]

def Test(Ensure, Instances):
    return [-1]

def GenerateInventoyMOF(Instances):
    header = ''
    footer= "\ninstance of OMI_ConfigurationDocument
	     {
                 DocumentType = "inventory";
                 Version="2.0.0";
                 MinimumCompatibleVersion = "2.0.0";
                 Name="InventoryConfig";
             };"

    inventoryMofSection = ''
    if Instances is not None:
        for instance in Instances:
            instanceName = instance['InstanceName']
            className = instance['ClassName']
            filepaths = ';\n'.join(instance['Properties'])
            new_source = 'instance of ' + className + '\n{\n'
            new_source+= filepaths + '\n};\n'
            inventoryMofSection+=new_source
    txt = header + inventoryMofSection + footer
    if os.path.isfile(inventoryMof_path): 
        shutil.copy2(inventoryMof_path, inventoryMof_path + '.bak')
    codecs.open(inventoryMof_path, 'w', 'utf8').write(txt)
    os.system('sudo /opt/microsoft/omsagent/bin/service_control restart')
