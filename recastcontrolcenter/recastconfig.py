import os
import pkg_resources
import yaml
import logging
log = logging.getLogger(__name__)


def default_config():
    return yaml.load(open(pkg_resources.resource_filename('recastcontrolcenter', 'resources/config.yaml')))


def mk_config():
    the_config = default_config()
    if 'RECASTCONTROLCENTER_CONFIG' in os.environ:
        custom_config = yaml.load(
            open(os.environ['RECASTCONTROLCENTER_CONFIG']))
        the_config.update(**custom_config)
    for k, v in os.environ.iteritems():
        if k.startswith('RECAST_'):
            the_config[k] = v
    # replicate RECAST_* back to shell env
    for k, v in the_config.iteritems():
        log.info('config value %s => %s', k, v)
        if not k.startswith('RECAST_'):
            raise ValueError(
                'configuration keys must starte with RECAST_!. change key: {}'.format(k))
        os.environ[k] = str(v)
    return the_config

config = mk_config()
