#!/usr/bin/python

import os, sys, logging, subprocess, urllib2
from optparse import OptionParser

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

##############################################################################
options = None
config = {}

##############################################################
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
    except urllib2.URLError, e:
        logging.error('URL_ERROR: %s' % e.reason)
    except:
        logging.exception('ERROR: exception')
    return o

##############################################################################
def check_devices():
    all_available = True
    for bt_dev in config['bluetooth_devices']:
        cmd = '%s %s' % (config['bluetooth_ping_command'], bt_dev)
        (ret, out) = run_wait(cmd)
        logging.debug(out)
        if ret:
            logging.debug('%s not available' % bt_dev)
        else:
            all_available = False
            logging.debug('%s available' % bt_dev)
            
    if all_available:
        logging.info('accessing vera_available_trigger_urls')
        for u in config['vera_available_trigger_urls']:
            logging.debug(u)
            open_url(u)
    else:
        logging.info('accessing vera_not_available_trigger_urls')
        for u in config['vera_not_available_trigger_urls']:
            logging.debug(u)
            open_url(u)

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
