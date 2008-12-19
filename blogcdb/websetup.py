"""Setup the boom application"""
import logging

import transaction
from tg import config

from blogcdb.config.environment import load_environment

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup boom here"""
    load_environment(conf.global_conf, conf.local_conf)
    # Load the models
    from blogcdb import model
    print "Creating tables"
    model.metadata.create_all(bind=config['pylons.app_globals'].sa_engine)

    u = model.User()
    u.user_name = u'peter'
    u.display_name = u'Peter Smith'
    u.email_address = u'peter@somedomain.com' #place a gravatar enabled email here
    u.password = u'peterpass'
    model.DBSession.add(u)

    u2 = model.User()
    u2.user_name = u'paul'
    u2.display_name = u'Paul Jones'
    u2.email_address = u'paul@somedomain.com'
    u2.password = u'paulpass'
    model.DBSession.add(u2)

    g = model.Group()
    g.group_name = u'blogusers'
    g.display_name = u'Blog User Group'

    g.users.append(u)
    g.users.append(u2)

    model.DBSession.add(g)

    p = model.Permission()
    p.permission_name = u'post'
    p.description = u'This permission give blog post usasge right to the bearer'
    p.groups.append(g)

    model.DBSession.add(p)

    model.DBSession.flush()

    transaction.commit()
    print "Successfully setup"
