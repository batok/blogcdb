"""Main Controller"""
from blogcdb.lib.base import BaseController
from tg import expose, flash, require, redirect, session
from pylons.i18n import ugettext as _
from repoze.what import predicates
from blogcdb.controllers.secc import Secc
from couchdb import Server
from couchdb import schema as sch
from couchdb.client import ResourceNotFound
from hashlib import md5
from datetime import datetime
import urllib

class Post(sch.Document):
    author = sch.TextField()
    subject = sch.TextField()
    content = sch.TextField()
    tags = sch.ListField( sch.TextField() )
    comments = sch.ListField( sch.DictField(sch.Schema.build(
        comment_author = sch.TextField(),
        comment = sch.TextField(),
        comment_date = sch.DateTimeField()
    )))    
    date = sch.DateTimeField()

class RootController(BaseController):
    
    secc = Secc()

    def getmail( self, user , format = "md5" ):
	mail = "domingo.aguilera@gmail.com"
        if format == "md5":
            email = md5(mail).hexdigest()
        else:
	    email = mail
        return email

    def getgravatar( self, user = "", size = "30"):
        html = "<span>&nbsp;</span>"
        if user:
            hash = self.getmail( user )
            mail = self.getmail( user, "foo")
            if mail:
            	html = "<img src='http://www.gravatar.com/avatar/%s?s=%s' />" % ( hash, size ) 
                
        return html

    @expose('blogcdb.templates.index')
    def index(self):
        return dict(page='index')


    @expose('blogcdb.templates.login')
    def login(self, **kw):
        came_from = kw.get('came_from', '/')
        return dict(page='login', header=lambda *arg: None,
                    footer=lambda *arg: None, came_from=came_from)
	
    @expose("json")
    def tags(self):
	blog = Server()["blog"]
        tags = []
        for row in blog.view("all/tags", group = True):
            tags.append( dict( blogtag = row.key) )
        return dict( identifier = "blogtag", items = tags )

    @expose(template="blogcdb.templates.blogpost")
    def blogpost(self):
        return dict(page = "New blog post")

    @expose(template="blogcdb.templates.postlist")
    #@require(predicates.has_permission('post'))
    def postlist(self , by_author = "",  tag = "", maxposts = "20", index = "1"):

        blog = Server()["blog"]
        posts = []
        view = "by_date"
        if by_author:
            view = "by_author"
            blogview = blog.view('all/%s' % view, key =  by_author, count = int(maxposts) )
        else:
            blogview = blog.view("all/%s" % view, descending = True, count = int(maxposts) )
        cuantos = 0   
        for row in blogview:
            cuantos += 1
            if cuantos > int(maxposts):
                break		
            goodOne = True
            if tag:
                if not tag in row.value["tags"]:
                    goodOne = False
            if goodOne:   
                posts.append(dict(author = row.value["author"], postid = row.value["_id"], subject = row.value["subject"], content = row.value["content"], postdate = row.value["date"], gravatar = self.getgravatar(row.value["author"])))
        return dict(  page = "postlist", posts = posts, by_author = by_author, tag = tag, newindex = int(index) + cuantos )
		

    @expose()
    def savepost(self, *args, **kwargs):
	user = "TEST"
        blog = Server()["blog"]
        p = Post( author = user, content = kwargs.get("content_field","Empty"), subject = kwargs.get("subject","Empty Subject"), date = datetime.now())
        p.tags.append("GENERAL")
        tag = kwargs.get("tag","")
        if tag:
            p.tags.append(tag)
        p.store(blog)
	redirect( "postlist")
    
    @expose()
    def savecomment(self, postid = "", content_field = "", **kw):
        user = "TEST"	
        if postid:
            blog = Server()["blog"]
            p = Post.load(blog,postid) 
            p.comments.append( dict(comment = content_field, comment_author = user, comment_date = datetime.now()) ) 
            p.store(blog)
            redirect("getpost?postid=%s" % postid)
        return dict() 

    @expose(template="blogcdb.templates.blogcomment")
    def blogcomment(self, postid=""):
        if not postid:
            raise redirect("/")
        return dict( page = "Blog Comment", postid = postid )

    @expose(template="blogcdb.templates.showpost")
    def getpost(self, postid = ""):
	print session
        if postid:
            blog = Server()["blog"]
            p = Post.load(blog,postid) 
            comments = []

            if p.comments:
                comments = p.comments 
	    for x in range(len(comments)):
                cual = comments[x]
                cual["gravatar"] = self.getgravatar( cual["comment_author"])
	    	cual["comment"] = u"<div>{0}</div>".format(cual["comment"])
            p2 = blog[postid]
            urls = []
            try:
                attachments = p2["_attachments"].keys()
	
            except:
                attachments= []
            for attachment in attachments:
                urls.append(urllib.urlencode(dict(attachment= attachment)))
	    content = u"<div>{0}</div>".format(p.content)
            return dict(  page = "Showing post", author = p.author, postid = p.id , subject = p.subject, postcontent =  content, tags = p.tags , postdate = p.date, comments = comments, attachments = attachments, urls = urls, gravatar = self.getgravatar(p.author)  )
        return dict() 

