#!/usr/bin/env python

"""
Commands work with servers. (Hiss, boo.)
"""

import copy
import logging

from fabric.api import local, put, settings, require, run, sudo, task
from fabric.state import env

import app_config

logging.basicConfig(format=app_config.LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(app_config.LOG_LEVEL)

"""
Setup
"""

@task
def setup():
    """
    Setup servers for deployment.

    This does not setup services or push to S3. Run deploy() next.
    """
    require('settings', provided_by=['production', 'staging'])
    require('branch', provided_by=['stable', 'master', 'branch'])

    if not app_config.DEPLOY_TO_SERVERS:
        logger.error('You must set DEPLOY_TO_SERVERS = True in your app_config.py before setting up the servers.')

        return

    create_directories()
    create_virtualenv()
    clone_repo()
    checkout_latest()
    install_requirements()
    setup_logs()

def create_directories():
    """
    Create server directories.
    """
    require('settings', provided_by=['production', 'staging'])

    run('mkdir -p %(SERVER_PROJECT_PATH)s' % app_config.__dict__)
    run('mkdir -p /var/www/uploads/%(PROJECT_FILENAME)s' % app_config.__dict__)

def create_virtualenv():
    """
    Setup a server virtualenv.
    """
    require('settings', provided_by=['production', 'staging'])

    run('virtualenv -p %(SERVER_PYTHON)s %(SERVER_VIRTUALENV_PATH)s' % app_config.__dict__)
    run('source %(SERVER_VIRTUALENV_PATH)s/bin/activate' % app_config.__dict__)

def clone_repo():
    """
    Clone the source repository.
    """
    require('settings', provided_by=['production', 'staging'])

    run('git clone %(REPOSITORY_URL)s %(SERVER_REPOSITORY_PATH)s' % app_config.__dict__)

    if app_config.REPOSITORY_ALT_URL:
        run('git remote add bitbucket %(REPOSITORY_ALT_URL)s' % app_config.__dict__)

@task
def checkout_latest(remote='origin'):
    """
    Checkout the latest source.
    """
    require('settings', provided_by=['production', 'staging'])
    require('branch', provided_by=['stable', 'master', 'branch'])

    run('cd %s; git fetch %s' % (app_config.SERVER_REPOSITORY_PATH, remote))
    run('cd %s; git checkout %s; git pull %s %s' % (app_config.SERVER_REPOSITORY_PATH, env.branch, remote, env.branch))

@task
def install_requirements():
    """
    Install the latest requirements.
    """
    require('settings', provided_by=['production', 'staging'])

    run('%(SERVER_VIRTUALENV_PATH)s/bin/pip install -U -r %(SERVER_REPOSITORY_PATH)s/requirements.txt' % app_config.__dict__)

@task
def setup_logs():
    """
    Create log directories.
    """
    require('settings', provided_by=['production', 'staging'])

    sudo('mkdir %(SERVER_LOG_PATH)s' % app_config.__dict__)
    sudo('chown ubuntu:ubuntu %(SERVER_LOG_PATH)s' % app_config.__dict__)

@task
def install_crontab():
    """
    Install cron jobs script into cron.d.
    """
    require('settings', provided_by=['production', 'staging'])

    sudo('cp %(SERVER_REPOSITORY_PATH)s/crontab /etc/cron.d/%(PROJECT_FILENAME)s' % app_config.__dict__)

@task
def uninstall_crontab():
    """
    Remove a previously install cron jobs script from cron.d
    """
    require('settings', provided_by=['production', 'staging'])

    sudo('rm /etc/cron.d/%(PROJECT_FILENAME)s' % app_config.__dict__)

def delete_project():
    """
    Remove the project directory. Invoked by shiva.
    """
    run('rm -rf %(SERVER_PROJECT_PATH)s' % app_config.__dict__)

"""
Fabcasting
"""

@task
def fabcast(command):
    """
    Actually run specified commands on the server specified
    by staging() or production().
    """
    require('settings', provided_by=['production', 'staging'])

    if not app_config.DEPLOY_TO_SERVERS:
        logging.error('You must set DEPLOY_TO_SERVERS = True in your app_config.py and setup a server before fabcasting.')

    run('cd %s && bash run_on_server.sh fab %s $DEPLOYMENT_TARGET %s' % (app_config.SERVER_REPOSITORY_PATH, env.branch, command))