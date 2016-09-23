#!/usr/bin/env python
#============================================================================
# Copyright (c) Microsoft Corporation. All rights reserved. See license.txt for license information.
#============================================================================
import os
import sys
import glob
#import pdb ; pdb.set_trace()

os.system('rm /tmp/omstest_cleanup* 2> /dev/null')
print 'Running test_OMS_nxProviders.py'
#Check and return if present
if not os.path.exists('/opt/micosoft/omsconfig'):
    os.system('touch /tmp/omstest_cleanup')
    bundle = sys.argv[1]
    
    bundle += '/omsagent*.universal.x64.sh' 
    bundle = glob.glob(bundle)[0]
    print 'Target = ' + bundle
    os.system('mkdir /tmp/omsext; cd /tmp/omsext ; ' + bundle + ' --extract')
    if os.system('which dpkg-deb') == 0:
        for pkg in glob.glob('/tmp/omsext/omsbundle*/100/*.deb'):
            os.system('dpkg-deb -x ' + pkg + ' /tmp/omsconfig')
    else:
        for pkg in glob.glob('/tmp/omsext/100/*.rpm'):
            os.system('cd /tmp/omsconfig; /rpm2cpio ' + pkg + ' | cpio -idmv')
    if not os.path.exists('/var/opt'):
        os.symlink('/tmp/omsconfig/var/opt','/var/opt')
    if not os.path.exists('/etc/opt'):
        os.symlink('/tmp/omsconfig/etc/opt','/etc/opt')
    if not os.path.exists('/opt/microsoft/omsconfig'):
        os.makedirs('/opt/microsoft')
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
    testpath = '/opt/microsoft/omsconfig/Scripts/' + sys.argv[2] + '/Scripts/Tests/'
    srcpath = '/SCX2/bld-omsagent/dsc/Providers/Scripts/' + sys.argv[2] + '/Scripts/Tests/ '
    os.system('cp ' + srcpath + '*test_OMS_nxProviders.py ' + testpath)
    os.system('cp ' + srcpath + '*dummy* ' + testpath)
    import pdb; pdb.set_trace()
    os.chdir(testpath)
    
    #Don't restart the service as it is not installed.
    os.system("echo '#!/bin/bash' > /tmp/omsconfig/opt/microsoft/omsagent/bin/service_control")
    #nxUser
    os.system('/usr/sbin/useradd  -c "JO JO MA,JOJOMA" -d "/home/jojoma" -m  -g mail jojoma')
    #nxGroup
    os.system('/usr/sbin/groupadd -g 1101 jojomamas')
    #nxPackage
    if os.system('which dpkg') == 0:
        os.system('/usr/bin/dpkg -i ' + testpath + 'dummy-1.0.deb')
    else:
        os.system('/usr/bin/rpm -i ' + testpath + 'dummy-1.0.deb')
result = os.system('su -c " python ' + testpath + 'test_OMS_nxProviders.py &> /tmp/test_nxOMSProviders_results.txt" omsagent')

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
if os.system('which dpkg') == 0:
    os.system('/usr/bin/dpkg -P dummy-1.0.deb')
else:
    os.system('/usr/bin/rpm -e dummy-1.0.deb')
os.system('rm -rf /tmp/omsext ; rm /tmp/omstest*')


sys.exit(0)
