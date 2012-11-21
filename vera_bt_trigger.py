#!/usr/bin/python

import os, sys, logging, subprocess, urllib2, json
from optparse import OptionParser

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

##############################################################################
options = None
config = {}

##############################################################################
def run_wait(cmd):
    logging.debug('executing: %s' % cmd)
    p = subprocess.Popen(cmd, shell=True, env=os.environ, 
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (stdout, stderr) = p.communicate()
    return (p.returncode, stdout)

##############################################################################
def open_url(url):
    try:
        r = urllib2.urlopen(url, timeout=10)
        o = r.read()
    except urllib2.HTTPError, e:
        logging.error('HTTP_ERROR: %s (%s)' % (e.code, e.msg))
        return None
    except urllib2.URLError, e:
        logging.error('URL_ERROR: %s' % e.reason)
        return None
    except:
        logging.exception('ERROR: exception')
        return None
    return o

##############################################################################
def get_device_status_from_json(json_string):
    data = json.loads(json_string)
    status = None
    try:
        for k in data.keys():
            if k.find('Device_Num_') == 0:
                for s in data[k]['states']:
                    if s['variable'] == 'Status':
                        status = s['value']
    except:
        status = None
    return status

##############################################################################
def check_devices():
    all_available = True
    for bt_dev in config['bluetooth_devices']:
        cmd = '%s %s' % (config['bluetooth_ping_command'], bt_dev)
        (ret, out) = run_wait(cmd)
        logging.debug(out)
        if ret:
            all_available = False
            logging.debug('%s not available' % bt_dev)
        else:
            logging.debug('%s available' % bt_dev)
            
    if all_available:
        logging.info('triggering vera_triggers -> available')
        devices = config['vera_triggers']['available']
    else:
        logging.info('triggering vera_triggers -> not_available')
        devices = config['vera_triggers']['not_available']
    
    for dev in devices:
        if dev['id'] == 'lu_action' and dev['action'] == 'SetTarget':
            url = '%s/data_request?output_format=json' % config['vera_url']
            status_url = '%s&id=status&DeviceNum=%s' % (url, dev['DeviceNum'])
            action_url = url
            for k, v in dev.items():
                action_url += '&%s=%s' % (k, v)
            logging.debug('status_url: %s' % status_url)
            logging.debug('action_url: %s' % action_url)
            status_json = open_url(status_url)
            if status_json is None:
                break
            status = get_device_status_from_json(status_json)
            logging.debug('current status: %s' % status)
            logging.debug('requested state: %s' % dev['newTargetValue'])
            if str(status) == str(dev['newTargetValue']):
                logging.info('no action on DeviceNum %s' % dev['DeviceNum'])
                break
            logging.info('triggering DeviceNum %s' % dev['DeviceNum'])
            open_url(action_url)
            

##############################################################################
def main():
    global options, config
    
    parser = OptionParser(usage='Usage: %prog [options]\n')
    
    # funtionality options
    parser.add_option('-c', '--config', default=None,
                      action='store', type='string', dest='config',
                      help='Configuration file')
    parser.add_option('-v', '--verbose', dest='verbose',
                      action='store_true', default=False,
                      help='Update its own record')
    (options, args) = parser.parse_args()
    
    # configure logging
    log_level = logging.INFO
    if options.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%y/%m/%d %H:%M:%S',
                        level=log_level)
    
    # read configuration file
    if options.config:
        if os.path.exists(options.config):
            config = load(file(options.config, 'r'), Loader=Loader)
        else:
            print('ERROR: configuration file %s does not exist' %
                  options.config)
            sys.exit(1)
    else:
        for cdir in [os.path.join('/', 'etc'),
                    os.path.dirname(__file__)]:
            config_file = os.path.join(cdir, 'vera_bt_trigger.yaml')
            if os.path.exists(config_file):
                config = load(file(config_file, 'r'), Loader=Loader)
                break
    
    check_devices()

##############################################################################
if __name__ == "__main__":
    main()

##############################################################################
