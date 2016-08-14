import os
import pkg_resources
import yaml

def default_config():
  return yaml.load(open(pkg_resources.resource_filename('recastcontrolcenter','resources/config.yaml')))

def mk_config():
    the_config = default_config()
    if os.environ.has_key('RECASTCONTROLCENTER_CONFIG'):
        custom_config = yaml.load(open(os.environ['RECASTCONTROLCENTER_CONFIG']))
        the_config.update(**custom_config)
    for k,v in os.environ.iteritems():
        if k.startswith('RECAST_'):
            the_config[k] = v
    return the_config

config = mk_config()
