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
try:
    import hashlib
    md5const = hashlib.md5
except ImportError:
    import md5
    md5const = md5.md5

inventoryMof_path = '/etc/opt/microsoft/omsagent/conf/omsagent.d/'
outputxml_path = '/etc/opt/omi/conf/omsconfig/configuration/'

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
    
def Set_Marshall(FeatureName, Enable = False, Instances = None, RunIntervalInSeconds = 300, Tag = "default", Format = "tsv", FilterType = "filter_changetracking", Configuration = None):
    init_vars(Instances)
    Set(FeatureName, Enable, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration)
    return [0]

def Test_Marshall(FeatureName, Enable = False, Instances = None, RunIntervalInSeconds = 300, Tag = "default", Format = "tsv", FilterType = "filter_changetracking", Configuration = None):
    init_vars(Instances)
    return Test(FeatureName, Enable, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration)

def Get_Marshall(FeatureName, Enable = False, Instances = None, RunIntervalInSeconds = 300, Tag = "default", Format = "tsv", FilterType = "filter_changetracking", Configuration = None):
    arg_names = list(locals().keys())
    init_vars(Instances)
    
    CurrentInstances = Instances
    FeatureName = protocol.MI_String(FeatureName)
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

           
def Set(FeatureName, Enable, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration):
    if Enable == True:
         GenerateInventoyMOF(FeatureName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration)
    else:
         mof_file_path = inventoryMof_path + FeatureName + '.mof'
         conf_file_path = inventoryMof_path + FeatureName + '.conf'
         if os.path.isfile(mof_file_path):
            os.remove(mof_file_path)

         if os.path.isfile(conf_file_path):
            os.remove(conf_file_path)
    return [0]



def Test(FeatureName, Enable, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration):

    shouldGenerateMofFile = TestGenerateInventoyMOF(FeatureName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration)

    shouldGenerateConfFile = TestGenerateInventoryConf(FeatureName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration)

    if(shouldGenerateMofFile or shouldGenerateConfFile):
        return [-1]

    return [0]



def GenerateInventoyMOFContents(FeatureName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration):
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
            new_source = 'instance of ' + className + ' as ' + instanceName +'\n{\n'
            new_source+= filepaths + ';\n};\n'
            inventoryMofSection+=new_source

    txt = header + inventoryMofSection + footer
    return txt


def GenerateInventoyConfContents(FeatureName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration):
    mof_file_path = inventoryMof_path + FeatureName + '.mof'
    conf_file_path = inventoryMof_path + FeatureName + '.conf'
    conf_file_contents = '#This is auto-generated file \n \
<source> \n \
  type exec \n \
  tag ' + Tag + ' \n \
  command /opt/microsoft/omsconfig/Scripts/PerformInventory.py --InMOF ' + mof_file_path + ' --OutXML ' + outputxml_path + FeatureName + '.xml > /dev/null && cat ' + outputxml_path + FeatureName + '.xml \n \
  format '+ Format + '\n \
  keys xml \n \
  run_interval ' + str(RunIntervalInSeconds) + 's \n \
</source> \n \
<filter '+ Tag + '> \n \
  type ' + FilterType + ' \n \
  # Force upload even if the data has not changed \n \
  force_send_run_interval 24h \n \
  log_level warn \n \
</filter> \n'
    return conf_file_contents


def TestGenerateInventoyMOF(FeatureName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration):
    mof_file_path = inventoryMof_path + FeatureName + '.mof'

    mof_file_contents = GenerateInventoyMOFContents(FeatureName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration)

    shouldGenerateMofFile = False
    if os.path.isfile(mof_file_path):
        filechecksum = GetFileChecksum (mof_file_path)
        stringchecksum = GetStringChecksum(mof_file_contents)
        if (filechecksum != stringchecksum):
           shouldGenerateMofFile = True
    else:
        shouldGenerateMofFile = True

    return shouldGenerateMofFile



def TestGenerateInventoryConf(FeatureName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration):

    conf_file_path = inventoryMof_path + FeatureName + '.conf'
    conf_file_contents = GenerateInventoyConfContents(FeatureName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration)

    shouldGenerateConfFile = False
    if os.path.isfile(conf_file_path):
        filechecksum = GetFileChecksum (conf_file_path)
        stringchecksum = GetStringChecksum(conf_file_contents)
        if (filechecksum != stringchecksum):
           shouldGenerateConfFile = True
    else:
        shouldGenerateConfFile = True

    return shouldGenerateConfFile



def GenerateInventoyMOF(FeatureName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration):
    mof_file_path = inventoryMof_path + FeatureName + '.mof'
    conf_file_path = inventoryMof_path + FeatureName + '.conf'

    mof_file_contents = GenerateInventoyMOFContents(FeatureName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration)

    conf_file_contents = GenerateInventoyConfContents(FeatureName, Instances, RunIntervalInSeconds, Tag, Format, FilterType, Configuration)

    codecs.open(mof_file_path, 'w', 'utf8').write(mof_file_contents)

    codecs.open(conf_file_path, 'w', 'utf8').write(conf_file_contents)

    os.system('sudo /opt/microsoft/omsagent/bin/service_control restart')


def GetFileChecksum(FilePath):
    checksum = md5const(open(FilePath, 'rb').read()).hexdigest()
    return checksum

def GetStringChecksum(inputString):
    checksum = md5const(inputString.encode('utf-8')).hexdigest()
    return checksum

