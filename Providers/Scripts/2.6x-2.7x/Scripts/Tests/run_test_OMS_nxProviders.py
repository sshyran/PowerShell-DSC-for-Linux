#!/usr/bin/env python
#============================================================================
# Copyright (c) Microsoft Corporation. All rights reserved. See license.txt for license information.
#============================================================================
import os
import sys
import glob
#import pdb ; pdb.set_trace()

os.system('rm /tmp/omstest_cleanup* 2> /dev/null')
os.system('rm -rf /tmp/omsext 2> /dev/null')

print 'Running test_OMS_nxProviders.py'
#Check and return if present
if not os.path.exists('/opt/micosoft/omsconfig'):
    os.system('touch /tmp/omstest_cleanup')
    bundle = sys.argv[1]
    
    bundle += '/omsagent*.universal.x64.sh' 
    bundle = glob.glob(bundle)[0]
    print 'Target = ' + bundle
    os.system('mkdir /tmp/omsext; cd /tmp/omsext ; ' + bundle + ' --extract')
    if os.system('which dpkg-deb &> /dev/null') == 0:
        for pkg in glob.glob('/tmp/omsext/omsbundle*/100/*.deb'):
            os.system('dpkg-deb -x ' + pkg + ' /tmp/omsconfig')
    else:
        for pkg in glob.glob('/tmp/omsext/100/*.rpm'):
            os.system('cd /tmp/omsconfig; /rpm2cpio ' + pkg + ' | cpio -idmv')
    os.chdir('/tmp/omsconfig/opt/microsoft/omsconfig/module_packages')
    for pkg in glob.glob('./*.zip'):
        os.system('unzip ' + pkg)
    
    if not os.path.exists('/var/opt'):
        os.symlink('/tmp/omsconfig/var/opt','/var/opt')
    if not os.path.exists('/etc/opt'):
        os.symlink('/tmp/omsconfig/etc/opt','/etc/opt')
    if not os.path.exists('/opt/microsoft/'):
        os.makedirs('/opt/microsoft/')
    if not os.path.exists('/opt/microsoft/omsconfig'):
        os.symlink('/tmp/omsconfig/opt/microsoft/omsconfig','/opt/microsoft/omsconfig')
    if os.system('grep -q "omsagent:" /etc/group'):
        os.system('groupadd -r omsagent')
        os.system('touch /tmp/omstest_cleanup_group')
        
    if os.system('grep -q "omsagent:" /etc/passwd'):
        os.system('useradd -r -c "OMS agent" -d /var/opt/microsoft/omsagent/run -g omsagent -s /bin/bash omsagent')
        os.system('touch /tmp/omstest_cleanup_user')
    
    os.system('echo "omsagent ALL=(ALL) NOPASSWD: `which python` " >> /tmp/omsconfig/etc/opt/microsoft/omsagent/sysconf/sudoers')
    os.system('cp /etc/sudoers /etc/sudoers.back')
    os.system('cat /tmp/omsconfig/etc/opt/microsoft/omsagent/sysconf/sudoers >> /etc/sudoers')
    os.system('chmod 440 /etc//sudoers')
    destpath = '/opt/microsoft/omsconfig/Scripts/' + sys.argv[2]
    import pdb; pdb.set_trace()
    srcpath = '/' + os.path.join(*os.path.realpath(__file__).split('/')[:-2]) + '/*'
    os.system('cp -r ' + srcpath + ' ' + destpath)
    os.chdir(destpath)
    
    #Don't restart the service as it is not installed.
    os.system("echo '#!/bin/bash' > /tmp/omsconfig/opt/microsoft/omsagent/bin/service_control")
    #nxUser
    os.system('/usr/sbin/useradd  -c "JO JO MA,JOJOMA" -d "/home/jojoma" -m  -g mail jojoma')
    #nxGroup
    os.system('/usr/sbin/groupadd -g 1101 jojomamas')
    #nxPackage
    if os.system('which dpkg 2> /dev/null') == 0:
        os.system('/usr/bin/dpkg -i ' + destpath + '/Scripts/Tests/dummy-1.0.deb')
    else:
        os.system('/usr/bin/rpm -i ' + destpath + '/Scripts/Tests/dummy-1.0.deb')
result = os.system('su -c " python ' + destpath + '/Scripts/Tests/test_OMS_nxProviders.py &> /tmp/test_nxOMSProviders_results.txt" omsagent')

if os.path.exists('/tmp/omstest_cleanup'):
    os.system('rm -rf /var/opt')
    os.system('rm -rf /etc/opt')
    os.system('rm -rf /opt/microsoft')
if os.path.exists('/tmp/omstest_cleanup_group'):
    os.system('groupdel omsagent')
if os.path.exists('/tmp/omstest_cleanup_user'):
    os.system('userdel omsagent')
os.system('cp /etc/sudoers.back /etc/sudoers')
os.system('chmod 440 /etc/sudoers')
if os.system('which dpkg 2> /dev/null') == 0:
    os.system('/usr/bin/dpkg -P dummy-1.0.deb')
else:
    os.system('/usr/bin/rpm -e dummy-1.0.deb')
os.system('rm -rf /tmp/omsext ; rm /tmp/omstest*')


sys.exit(0)
