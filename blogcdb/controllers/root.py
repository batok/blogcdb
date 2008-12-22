"""Main Controller"""
from blogcdb.lib.base import BaseController
from tg import expose, flash, require, redirect, session, response, request
from pylons.i18n import ugettext as _
from repoze.what import predicates
from blogcdb.controllers.secc import Secc
from couchdb import Server
from couchdb import schema as sch
from couchdb.client import ResourceNotFound
from hashlib import md5
from datetime import datetime
import urllib
import cStringIO as StringIO
from blogcdb.model import User
from pylons import config

map_func_tags = """
function(doc) {
	for ( i in doc.tags) emit(doc.tags[i], 1);
}
"""

reduce_func_tags = """
function( keys, values) {
	return sum(values);
}
"""

map_func_attachments = """
function(doc) {
	for ( i in doc._attachments) emit(i, [doc._id, doc.author]);
}
"""

map_func_by_author= """
function(doc){
	emit(doc.author, doc);
}
"""

map_func_by_date= """
function(doc){
	emit(doc.date, doc);
}
"""

map_func_all = """
function(doc){
	emit(null, doc);
}
"""

def cdb():
	couchdb_database = "blog"
	couchdb_url = "http://127.0.0.1:5984"
	try:
		couchdb_database = config.get("couchdb.database",couchdb_database)
		couchdb_url = config.get("couchdb.url",couchdb_url)
	except:
		print "There was an error getting configuration data"

	return Server( couchdb_url )[couchdb_database]

def createdatabase():
	couchdb_database = "blog"
	couchdb_url = "http://127.0.0.1:5984"
	try:
		couchdb_database = config.get("couchdb.database",couchdb_database)
		couchdb_url = config.get("couchdb.url",couchdb_url)
	except:
		print "There was an error getting configuration data"

	created = True
	try:
		Server( couchdb_url ).create(couchdb_database)
	
	except:
		created = False
	return created

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

class Design( sch.Document):
	by_author = sch.View("all", map_func_by_author) 
	by_date = sch.View("all", map_func_by_date) 
	all = sch.View("all", map_func_all) 
	tags = sch.View("all", map_func_tags, reduce_func_tags) 
	attachments = sch.View("all", map_func_attachments)

class RootController(BaseController):
    
	secc = Secc()
	def getuser(self):
		try:
			return request.environ.get('repoze.who.identity')['repoze.who.userid']
		except:
			return ""

	def getmail( self, user , format = "md5" ):
		try:
			mail = User.by_user_name( user ).email_address
			print mail
		except:
			mail = "whitedwarfwillbeoursun@gmail.com"

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
		if createdatabase():
			from couchdb.design import ViewDefinition
			blog = cdb()
			ViewDefinition.sync_many( blog, [Design.all, Design.by_date, Design.by_author, Design.tags, Design.attachments])
			p = Post()
			p.author = "peter"
			p.subject = "Welcome Blog Post"
			p.content = "First Post by <b>Peter</b>."
			p.date = datetime.now()
			p.tags = ["GENERAL", "WELCOME"]
			p.store(blog)

        	return dict(page='index')


    	@expose('blogcdb.templates.login')
    	def login(self, **kw):
        	came_from = kw.get('came_from', '/')
        	return dict(page='login', header=lambda *arg: None, footer=lambda *arg: None, came_from=came_from)
	
    	@expose("json")
    	@require(predicates.has_permission('post'))
    	def tags(self):
		blog = cdb()
        	tags = []
        	for row in blog.view("all/tags", group = True):
            		tags.append( dict( blogtag = row.key) )
        	return dict( identifier = "blogtag", items = tags )

	@expose(template="blogcdb.templates.blogpost")
    	@require(predicates.has_permission('post'))
    	def blogpost(self):
        	return dict(page = "New blog post")



    	@expose(template="blogcdb.templates.postlist")
    	@require(predicates.has_permission('post'))
    	def postlist(self , by_author = "",  tag = "", maxposts = "20", index = "1"):

		user = self.getuser()

		blog = cdb()
        	posts = []
        	view = "by_date"
        	if by_author:
            		view = "by_author"
            		blogview = blog.view('all/%s' % view, key =  by_author, count = int(maxposts) )
        	else:
            		blogview = blog.view("all/%s" % view, descending = True, count = int(maxposts) )
        	howmany = 0   
        	for row in blogview:
            		howmany += 1
            		if howmany > int(maxposts):
                		break		
            		goodOne = True
            		if tag:
                		if not tag in row.value["tags"]:
                   			 goodOne = False
            		if goodOne:   
                		posts.append(dict(author = row.value["author"], postid = row.value["_id"], subject = row.value["subject"], content = row.value["content"], postdate = row.value["date"], gravatar = self.getgravatar(row.value["author"])))
        	return dict(  page = "postlist", posts = posts, by_author = by_author, tag = tag, newindex = int(index) + howmany)
		

    	@expose()
    	@require(predicates.has_permission('post'))
    	def savepost(self, *args, **kwargs):

		user = self.getuser()
		blog = cdb()
        	p = Post( author = user, content = kwargs.get("content_field","Empty"), subject = kwargs.get("subject","Empty Subject"), date = datetime.now())
        	p.tags.append("GENERAL")
        	tag = kwargs.get("tag","")
        	if tag:
            		p.tags.append(tag)
        	p.store(blog)
		redirect( "postlist")
    
    	@expose()
    	@require(predicates.has_permission('post'))
    	def savecomment(self, postid = "", content_field = "", **kw):
		user = self.getuser()
        	if postid:
			blog = cdb()
            		p = Post.load(blog,postid) 
            		p.comments.append( dict(comment = content_field, comment_author = user, comment_date = datetime.now()) ) 
            		p.store(blog)
            		redirect( str(u"getpost?postid=%s" % postid))
        	return dict() 

    	@expose(template="blogcdb.templates.blogcomment")
    	@require(predicates.has_permission('post'))
    	def blogcomment(self, postid=""):
        	if not postid:
            		redirect("/")
        	return dict( page = "Blog Comment", postid = postid )

    	@expose(template="blogcdb.templates.showpost")
    	@require(predicates.has_permission('post'))
    	def getpost(self, postid = ""):
        	if postid:
			blog = cdb()
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

    	@expose()
    	@require(predicates.has_permission('post'))
    	def addtag(self, tag="", postid = ""):

        	if tag and postid:
			blog = cdb()
            		tag = tag.upper()
            		p = Post.load(blog, postid)
            		if tag not in ( p.tags ):
                		p.tags.append( tag )
                		p.store(blog)
            		redirect( str(u"getpost?postid=%s" % postid))
        	redirect( "listposts" ) 

    	@expose()
    	@require(predicates.has_permission('post'))
    	def download(self, postid="", attachment=""):

		blog = cdb()
        	if attachment and postid:
            		doc = blog[postid]
            		f = StringIO.StringIO(blog.get_attachment(doc, attachment))
            		response.headers["Content-Type"] = doc["_attachments"][attachment]["content_type"]
            		response.headers["Content-Disposition"] = "attachment; filename=" + attachment
            		return f.getvalue()

        	redirect("/")
            
    	@expose()
    	@require(predicates.has_permission('post'))
    	def thumbnail(self, postid="", attachment=""):
        	if attachment and postid:
            		if attachment.endswith("jpg") or attachment.endswith("jpeg") or attachment.endswith("JPG") or attachment.endswith("JPEG"):
                		pass
            		else:
            			redirect("/images/attachment-icon.jpg")
			blog = cdb()

            		doc = blog[postid]
            		f = StringIO.StringIO(blog.get_attachment(doc, attachment))
            		f2 = StringIO.StringIO()
            		from PIL import Image
            		im = Image.open(f)
			w, h = im.size
			rh = int(h/64)
			rw = int(w/64)
			nw = nh = 64
			if rw and rh:
				nw = w / rw
				nh = h / rh

            		size = nw, nh
            		im.thumbnail(size,Image.ANTIALIAS)
            		im.save(f2, "JPEG")            
            		response.headers["Content-Type"] = doc["_attachments"][attachment]["content_type"]
            		return f2.getvalue()
        	redirect("/")

    	@expose(template="blogcdb.templates.blogupload")
    	@require(predicates.has_permission('post'))
    	def blogupload(self, postid=""):
        	if not postid:
            		redirect("/")
        	return dict( page = "file attachment", postid = postid )

    	@expose()
    	@require(predicates.has_permission('post'))
    	def upload(self, postid = "", upload_file = "", submit_upload = ""):
        	if postid:
			blog = cdb()
            		doc = blog[postid]
            		xfilename = upload_file.filename
            		filename = xfilename.split("\\")[-1]
            		f = StringIO.StringIO(upload_file.file.read())
            		blog.put_attachment(doc, f, filename)
            		redirect( str(u"getpost?postid=%s" % postid))
        	redirect("/")
