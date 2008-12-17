"""Setup the blogcdb application"""
import logging

import transaction
from tg import config

from blogcdb.config.environment import load_environment

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup blogcdb here"""
    load_environment(conf.global_conf, conf.local_conf)
    # Load the models
    from blogcdb import model
    print "Creating tables"
    model.metadata.create_all(bind=config['pylons.app_globals'].sa_engine)

    u = model.User()
    u.user_name = u'joe'
    u.display_name = u'Joe Last Name'
    u.email_address = u'joe@blogcdb.com'
    u.password = u'joesecret'

    model.DBSession.add(u)

    g = model.Group()
    g.group_name = u'couchdbusers'
    g.display_name = u'Couchdb users Group'

    g.users.append(u)

    model.DBSession.add(g)

    p = model.Permission()
    p.permission_name = u'post'
    p.description = u'This permission give post right to the bearer'
    p.groups.append(g)

    model.DBSession.add(p)

    u1 = model.User()
    u1.user_name = u'Jane'
    u1.display_name = u'Jane Last Name'
    u1.email_address = u'jane@blogcdb.com'
    u1.password = u'janesecret'

    model.DBSession.add(u1)
    model.DBSession.flush()

    transaction.commit()
    print "Successfully setup"
