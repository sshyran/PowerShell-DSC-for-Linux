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
import hashlib

protocol = imp.load_source('protocol', '../protocol.py')
nxDSCLog = imp.load_source('nxDSCLog', '../nxDSCLog.py')

LG = nxDSCLog.DSCLog

inventoryMof_path = '/etc/opt/microsoft/omsagent/conf/omsagent.d/'

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
    
def Set_Marshall(FileName, Enable = False, Instances = None, RunIntervalInSeconds = 300, Tag = "default", Format = "tsv", FilterType = "filter_changetracking", Configuration = None):
    init_vars(Instances)
    Set(FileName, Enable, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration)
    return [0]

def Test_Marshall(FileName, Enable = False, Instances = None, RunIntervalInSeconds = 300, Tag = "default", Format = "tsv", FilterType = "filter_changetracking", Configuration = None):
    init_vars(Instances)
    return Test(Enable, Instances)

def Get_Marshall(FileName, Enable = False, Instances = None, RunIntervalInSeconds = 300, Tag = "default", Format = "tsv", FilterType = "filter_changetracking", Configuration = None):
    arg_names = list(locals().keys())
    init_vars(Instances)
    
    CurrentInstances = Instances
    FileName = protocol.MI_String(FileName)
    Enable = protocol.MI_Boolean(Enable)
    for instance in CurrentInstances:
        instance['InstanceName'] = protocol.MI_String(instance['InstanceName'])
        instance['ClassName'] = protocol.MI_String(instance['ClassName'])
        if instance['Properties'] is not None and len(instance['Properties']):
            instance['Properties'] = protocol.MI_StringA(instance['Properties'])
    Instances = protocol.MI_InstanceA(CurrentInstances)
    RunIntervalInSeconds = protocol.MI_Uint64(RunIntervalInSeconds)
    Tag = protocol.MI_String(Tag)
    Format = protocol.MI_String(Format)
    FilterType = protocol.MI_String(FilterType)

    if Configuration is None:
        Configuration = []
    if Configuration is not None and len(Configuration):
        Configuration = protocol.MI_StringA(Configuration)

    retd = {}
    ld = locals()
    for k in arg_names:
        retd[k] = ld[k]
    return 0, retd
            
def Set(FileName, Enable, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration):
    if Enable == True:
         GenerateInventoyMOF(FileName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration)
    return [0]

def Test(Enable, Instances):
    return [-1]

def GenerateInventoyMOF(FileName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration):
    header = '/*This is an autogenerated file \n@TargetNode=\'Localhost\'*/\n'
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
            new_source+= filepaths + ';\n};\n'
            inventoryMofSection+=new_source

    mof_file_path = inventoryMof_path + FileName
    txt = header + inventoryMofSection + footer 

    mofFileWritten = False
    if os.path.isfile(mof_file_path): 
        filechecksum = GetFileChecksum (mof_file_path)
        stringchecksum = GetStringChecksum(txt)
        if (filechecksum != stringchecksum):
           codecs.open(mof_file_path, 'w', 'utf8').write(txt)
           mofFileWritten = True
    else:
        codecs.open(mof_file_path, 'w', 'utf8').write(txt)
        mofFileWritten = True


    fileNameWithoutExtension = os.path.splitext(FileName)[0] 
    conf_file_path = inventoryMof_path+ fileNameWithoutExtension + '.conf'
    conf_file_contents = '#This is auto-generated file \n \
<source> \n \
  type exec \n \
  tag ' + Tag + ' \n \
  command /opt/microsoft/omsconfig/Scripts/PerformInventory.py --InMOF ' + mof_file_path + ' --OutXML /etc/opt/omi/conf/omsconfig/configuration/' + fileNameWithoutExtension + '.xml > /dev/null && cat /etc/opt/omi/conf/omsconfig/configuration/' + fileNameWithoutExtension + '.xml \n \
  format tsv \n \
  keys xml \n \
  run_interval ' + str(RunIntervalInSeconds) + 's \n \
</source> \n \
<filter '+ Tag + '> \n \
  type ' + FilterType + ' \n \
  # Force upload even if the data has not changed \n \
  force_send_run_interval 24h \n \
  log_level warn \n \
</filter> \n'

    confFileWritten = False
    if os.path.isfile(conf_file_path): 
        filechecksum = GetFileChecksum (conf_file_path)
        stringchecksum = GetStringChecksum(conf_file_contents)
        if (filechecksum != stringchecksum):
           codecs.open(conf_file_path, 'w', 'utf8').write(conf_file_contents)
           confFileWritten = True
    else:
        codecs.open(conf_file_path, 'w', 'utf8').write(conf_file_contents)
        confFileWritten = True

    if (mofFileWritten or confFileWritten):
       os.system('sudo /opt/microsoft/omsagent/bin/service_control restart')

    return txt

def GetFileChecksum(FilePath):
    checksum = hashlib.md5(open(FilePath, 'rb').read()).hexdigest()
    return checksum

def GetStringChecksum(inputString):
    checksum = hashlib.md5(inputString.encode('utf-8')).hexdigest()
    return checksum
