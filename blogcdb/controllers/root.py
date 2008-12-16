"""Main Controller"""
from blogcdb.lib.base import BaseController
from tg import expose, flash, require
from pylons.i18n import ugettext as _
#from tg import redirect, validate
#from blogcdb.model import DBSession, metadata
#from dbsprockets.dbmechanic.frameworks.tg2 import DBMechanic
#from dbsprockets.saprovider import SAProvider
from repoze.what import predicates
from blogcdb.controllers.secc import Secc

class RootController(BaseController):
    #admin = DBMechanic(SAProvider(metadata), '/admin')
    secc = Secc()

    @expose('blogcdb.templates.index')
    def index(self):
        return dict(page='index')

    @expose('blogcdb.templates.about')
    def about(self):
        return dict(page='about')

    @expose('blogcdb.templates.authentication')
    def auth(self):
        return dict(page='auth')

    @expose('blogcdb.templates.index')
    @require(predicates.has_permission('manage'))
    def manage_permission_only(self, **kw):
        return dict(page='managers stuff')

    @expose('blogcdb.templates.index')
    @require(predicates.is_user('editor'))
    def editor_user_only(self, **kw):
        return dict(page='editor stuff')

    @expose('blogcdb.templates.login')
    def login(self, **kw):
        came_from = kw.get('came_from', '/')
        return dict(page='login', header=lambda *arg: None,
                    footer=lambda *arg: None, came_from=came_from)
