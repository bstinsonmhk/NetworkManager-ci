#
# This script uses the Duffy node management api to get fresh machines to run
# your CI tests on. Once allocated you will be able to ssh into that machine
# as the root user and setup the environ
#
# XXX: You need to add your own api key below, and also set the right cmd= line
#      needed to run the tests
#
# Please note, this is a basic script, there is no error handling and there are
# no real tests for any exceptions. Patches welcome!

import json, urllib, subprocess, sys, os

def get_testmapper(testbranch):
    if not os.path.isfile('testmapper.txt'):
        testmapper_url = 'https://raw.githubusercontent.com/NetworkManager/NetworkManager-ci/\%s/testmapper.txt' % (testbranch)
        os.system("wget -q  %s -O testmapper.txt" % testmapper_url)

def get_test_cases_for_features(features, testbranch):
    get_testmapper(testbranch)
    testnames = []
    with open('testmapper.txt', 'r') as f:
        content = f.readlines()
        for feature_name in features:
            processing = False
            for line in content:
                if line.strip().startswith('#@%s_start' % feature_name):
                    processing = True
                    continue
                if line.strip().startswith('#@%s_end' % feature_name):
                    break
                if line.strip().startswith('#') :
                    continue
                line_csv = line.split(',')
                if processing and len(line_csv) >= 3:
                    test_name = line_csv[0].strip()
                    if test_name and test_name not in testnames:
                        testnames.append(test_name)
    subprocess.call('rm -rf testmapper.txt', shell=True)
    return testnames

def precess_raw_features(features, testbranch):
    tests = ""
    if not features or features.lower() == 'all':
        raw_features = 'adsl,alias,bond,bridge,connection,dispatcher,ethernet,general,ipv4,ipv6,libreswan,openvpn,ppp,pptp,team,tuntap,vlan,vpnc'
    else:
        raw_features = features
    features = []
    for f in raw_features.split(','):
        features.append(f.strip())
    for test in get_test_cases_for_features(features, testbranch):
        tests=tests+test+" "
    return tests.strip()

url_base="http://admin.ci.centos.org:8080"

# This file was generated on your slave.  See https://wiki.centos.org/QaWiki/CI/GettingStarted
api=open('/home/networkmanager/duffy.key').read().strip()

ver="7"
arch="x86_64"
count=1

get_nodes_url="%s/Node/get?key=%s&ver=%s&arch=%s&count=%s" % (url_base,api,ver,arch,count)

dat=urllib.urlopen(get_nodes_url).read()
b=json.loads(dat)

tests=precess_raw_features("all", "master")

for h in b['hosts']:
    cmd0="ssh -t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@%s 'yum install -y git \
                                               && git clone https://github.com/NetworkManager/NetworkManager-ci \
                                               && cd NetworkManager-ci \
                                               && git checkout vb/cico \
                                               && sh run/centos-ci/scripts/./setup.sh \
                                               && sh run/centos-ci/scripts/./build.sh nm-1-6 \
                                               && sh run/centos-ci/scripts/./get_tests.sh master \
                                               && sh run/centos-ci/scripts/./runtest.sh %s'" % (h, tests)
    print cmd0
    rtn_code=subprocess.call(cmd0, shell=True)
    print h
    # cmd="ssh -t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@%s 'run/fedora-vagrant/scripts/./setup.sh'" % (h)
    # print cmd
    # rtn_code=subprocess.call(cmd, shell=True)
    # cmd2="ssh -t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@%s 'run/fedora-vagrant/scripts/./build.sh nm-1-6'" % (h)
    # print cmd2
    # rtn_code=subprocess.call(cmd2, shell=True)
    # cmd3="ssh -t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@%s 'run/fedora-vagrant/scripts/./get_tests.sh master'" % (h)
    # print cmd3
    # rtn_code=subprocess.call(cmd3, shell=True)
    # cmd4="ssh -t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@%s 'run/fedora-vagrant/scripts/./runtest.sh ipv6_never-default_remove'" % (h)
    # print cmd4
    # rtn_code=subprocess.call(cmd4, shell=True)


done_nodes_url="%s/Node/done?key=%s&ssid=%s" % (url_base, api, b['ssid'])
das=urllib.urlopen(done_nodes_url).read()

sys.exit(rtn_code)