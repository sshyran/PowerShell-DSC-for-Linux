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
            if instance['Properties'] is not None and len(instance['Properties'].value) > 0:
                for property in instance['Properties'].value:
                    if property is not None and len(property) > 0:
                        new_properties.append(property)

            if len(new_properties) > 0:
                instance['Properties'] = new_properties
                new_instances.append(instance)

    Instances = new_instances
    
def Set_Marshall(FilePath, Ensure = False, Instances = None):
    init_vars(Instances)
    Set(FilePath, Ensure, Instances)
    return [0]

def Test_Marshall(FilePath, Ensure = False, Instances = None):
    init_vars(Instances)
    return Test(Ensure, Instances)

def Get_Marshall(FilePath, Ensure = False, Instances = None):
    arg_names = list(locals().keys())
    init_vars(Instances)
    
    CurrentInstances = Instances
    FilePath = protocol.MI_String(FilePath)
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
            
def Set(FilePath, Ensure, Instances):
    if Ensure == True:
         GenerateInventoyMOF(FilePath, Instances)
    return [0]

def Test(Ensure, Instances):
    return [-1]

def GenerateInventoyMOF(FilePath, Instances):
    header = '/*@TargetNode=\'Localhost\'*/\n'
    footer= '\ninstance of OMI_ConfigurationDocument \n{\n \
    DocumentType = \"inventory\"; \n \
    Version=\"2.0.0\"; \n \
    MinimumCompatibleVersion = \"2.0.0\"; \n \
    Name=\"InventoryConfig\"; \n};'

    inventoryMofSection = ''
    if Instances is not None:
        for instance in Instances:
            instanceName = instance['InstanceName']
            className = instance['ClassName']
            filepaths = '    '+';\n    '.join(instance['Properties'])
            new_source = 'instance of ' + className + '\n{\n'
            new_source+= filepaths + '\n};\n'
            inventoryMofSection+=new_source

    if os.path.isfile(FilePath): 
        shutil.copy2(FilePath, FilePath + '.bak')
    txt = header + inventoryMofSection + footer 
    codecs.open(FilePath, 'w', 'utf8').write(txt)
    print(FilePath)
    print(txt)

    
    conffilename = os.path.splitext(FilePath)[0] + '.conf'
    conffilecontents = '#This is auto-generated file \n \
<source> \n \
  type exec \n \
  tag oms.changetracking \n \
  command /opt/microsoft/omsconfig/Scripts/PerformInventory.py --InMOF ' + FilePath + ' --OutXML /etc/opt/omi/conf/omsconfig/configuration/ChangeTrackingInventory.xml > /dev/null && cat /etc/opt/omi/conf/omsconfig/configuration/ChangeTrackingInventory.xml \n \
  format tsv \n \
  keys xml \n \
  run_interval 300s \n \
</source> \n \
<filter oms.changetracking> \n \
  type filter_changetracking \n \
  # Force upload even if the data has not changed \n \
  force_send_run_interval 24h \n \
  log_level warn \n \
</filter>'

    print("Conf file path" + conffilename)
    if os.path.isfile(conffilename): 
        shutil.copy2(conffilename, conffilename + '.bak')

    codecs.open(conffilename, 'w', 'utf8').write(conffilecontents)
    return txt
#    os.system('sudo /opt/microsoft/omsagent/bin/service_control restart')
