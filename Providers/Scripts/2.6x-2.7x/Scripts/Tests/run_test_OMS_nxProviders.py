#!/usr/bin/env python
#============================================================================
# Copyright (c) Microsoft Corporation. All rights reserved. See license.txt for license information.
#============================================================================
import os
import sys
import glob


#???
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
    os.system('cp -r  /tmp/omsconfig/opt/microsoft/omsconfig/module_packages/*/DSCResources/*/x*/Scripts/* /tmp/omsconfig/opt/microsoft/omsconfig/Scripts/')
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
    
    os.system('mkdir -p /tmp/omsconfig/etc/opt/omi/conf/omsconfig')
    os.system('chmod 700 /tmp/omsconfig/etc/opt/omi/conf/omsconfig')
    os.system('chmod a+rx /tmp/omsconfig/etc/opt/omi/conf/omsconfig/')
    os.system('chown -R omsagent /tmp/omsconfig/etc/opt/omi/conf/omsconfig')
    os.system('chown -R omsagent /tmp/omsconfig/opt/microsoft/omsconfig/Scripts')
    os.system('su - omsagent -c "/tmp/omsconfig/opt/microsoft/omsconfig/Scripts/RegenerateInitFiles.py"')
    os.system('su - omsagent -c "/tmp/omsconfig/opt/microsoft/omsconfig/Scripts/ImportGPGKey.sh /tmp/omsconfig/opt/microsoft/omsconfig/keys/msgpgkey.asc keymgmtring.gpg"')
    os.system('su - omsagent -c "/tmp/omsconfig/opt/microsoft/omsconfig/Scripts/ImportGPGKey.sh /tmp/omsconfig/opt/microsoft/omsconfig/keys/dscgpgkey.asc keyring.gpg"')
    os.system('mkdir -p /tmp/omsconfig/var/opt/microsoft/omsconfig')
    os.system('chown omsagent /tmp/omsconfig/var/opt/microsoft/omsconfig')
    os.system('chgrp omsagent /tmp/omsconfig/var/opt/microsoft/omsconfig')
    os.system('touch /tmp/omsconfig/var/opt/microsoft/omsconfig/syslog-ng-oms.conf')
    os.system('touch /tmp/omsconfig/var/opt/microsoft/omsconfig/rsyslog-oms.conf')
    if os.path.exists('/etc/rsyslog.d/'):
        os.system('cp /tmp/omsconfig/etc/opt/microsoft/omsagent/sysconf/rsyslog.conf /tmp/omsconfig/etc/rsyslog.d/95-omsagent.conf')
        os.system('chown omsagent:omsagent /tmp/omsconfig/etc/rsyslog.d/95-omsagent.conf')
    
    os.system('echo "omsagent ALL=(ALL) NOPASSWD: `which python` " >> /tmp/omsconfig/etc/opt/microsoft/omsagent/sysconf/sudoers')
    os.system('cp /etc/sudoers /etc/sudoers.back')
    os.system('cat /tmp/omsconfig/etc/opt/microsoft/omsagent/sysconf/sudoers >> /etc/sudoers')
    os.system('chmod 440 /etc/sudoers')
    # copy the Tests
    destpath = '/tmp/omsconfig/opt/microsoft/omsconfig/Scripts/' + sys.argv[2] + '/Scripts/'
    srcpath = '/' + os.path.join(*os.path.realpath(__file__).split('/')[:-1])
    os.system('cp -r ' + srcpath + ' ' + destpath)
    os.chdir(destpath + 'Tests')
    #Don't restart the service as it is not installed.
    os.system("echo '#!/bin/bash' > /tmp/omsconfig/opt/microsoft/omsagent/bin/service_control")
    #nxUser
    os.system('/usr/sbin/useradd -d "/home/jojoma" -m  -g mail jojoma')
    os.system('/usr/sbin/usemod -c "JO JO MA,JOJOMA" jojoma')
    #nxGroup
    os.system('/usr/sbin/groupadd -g 1101 jojomamas')
    #nxPackage
    if os.system('which dpkg 2> /dev/null') == 0:
        os.system('/usr/bin/dpkg -i ' + destpath + 'Tests/dummy-1.0.deb')
    else:
        os.system('/usr/bin/rpm -i ' + destpath + 'Tests/dummy-1.0-1.x86_64.rpm')
result = os.system('su -c " python ' + destpath + 'Tests/test_OMS_nxProviders.py" omsagent')
#result = os.system('su -c " python ' + destpath + 'Tests/test_OMS_nxProviders.py &> /tmp/test_nxOMSProviders_results.txt" omsagent')

if os.path.exists('/tmp/omstest_cleanup'):
    os.system('rm -rf /var/opt')
    os.system('rm -rf /etc/opt')
    os.system('rm -rf /opt/microsoft')
if os.path.exists('/tmp/omstest_cleanup_group'):
    os.system('groupdel omsagent')
    os.system('groupdel jojomamas')
if os.path.exists('/tmp/omstest_cleanup_user'):
    os.system('userdel omsagent')
    os.system('userdel jojoma')
os.system('cp /etc/sudoers.back /etc/sudoers')
os.system('chmod 440 /etc/sudoers')
if os.system('which dpkg 2> /dev/null') == 0:
    os.system('/usr/bin/dpkg -P dummy')
else:
    os.system('/usr/bin/rpm -e dummy')
os.system('rm -rf /tmp/omsext ; rm /tmp/omstest*')
os.system('rm -rf /tmp/omsconfig')


sys.exit(0)
