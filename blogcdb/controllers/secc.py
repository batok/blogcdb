"""Test Secure Controller"""
from blogcdb.lib.base import BaseController
from tg import expose, flash
from pylons.i18n import ugettext as _
#from tg import redirect, validate
#from blogcdb.model import DBSession, metadata
#from dbsprockets.dbmechanic.frameworks.tg2 import DBMechanic
#from dbsprockets.saprovider import SAProvider
from repoze.what.predicates import has_permission


class Secc(BaseController):
    """Sample controller-wide authorization"""

    # The predicate that must be met for all the actions in this controller:
    allow_only = has_permission('manage')

    @expose('blogcdb.templates.index')
    def index(self):
        flash(_("Secure Controller here"))
        return dict(page='index')

    @expose('blogcdb.templates.index')
    def some_where(self):
        """should be protected because of the require attr
        at the controller level.
        """
        return dict(page='some_where')
