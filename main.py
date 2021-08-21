from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import json
import math

with open('config.json', 'r') as cnf:
    parameter = json.load(cnf)["params"]

local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = parameter['gmail_username'],
    MAIL_PASSWORD = parameter['gmail_password']
)
mail = Mail(app)
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameter['local_url']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameter['prod_url']

db = SQLAlchemy(app)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    mobile = db.Column(db.String(12), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    time = db.Column(db.String(120), nullable=True)

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
    posted_by = db.Column(db.String(15), nullable=True)
    img_file = db.Column(db.String(15), nullable=True)
    date = db.Column(db.String(120), nullable=True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().order_by(Posts.id.desc()).all()
    last = math.ceil(len(posts) / int(parameter['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[
            (page - 1) * int(parameter['no_of_posts'])
            :(page - 1) * int(parameter['no_of_posts']) +
             int(parameter['no_of_posts'])]
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', parameter=parameter, posts=posts, prev=prev, next=next)

@app.route("/blog/<string:blog_slug>", methods=['GET'])
def blog(blog_slug):
    post = Posts.query.filter_by(slug=blog_slug).first()
    return render_template('blog.html', parameter=parameter,post=post)

@app.route("/about-us")
def about():
    return render_template('about-us.html', parameter=parameter)

@app.route("/contact-us", methods=['GET','POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        message = request.form.get('message')
        insert=Contact(name=name, mobile=mobile, email=email, msg=message,time=datetime.now())
        db.session.add(insert)
        db.session.commit()
        mail.send_message('New message from ' + name,sender=email,recipients=[parameter['gmail_username']],
                          body=message + "\n" + mobile)
        flash("Your Message received, we will contact you soon", "success")
    return render_template('contact.html', parameter=parameter)

@app.route("/admin/dashboard", methods = ['GET', 'POST'])
def login():
    if ('user' in session and session['user'] == parameter['admin_user']):
        posts = Posts.query.all()
        return render_template('/admin/dashboard.html', parameter=parameter,posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('upass')
        if (username == parameter['admin_user'] and userpass == parameter['admin_password']):
            session['user'] = username
            posts=Posts.query.all()
            return render_template('/admin/dashboard.html', parameter=parameter, posts=posts)
        flash("Please Enter Correct Username Or Password", "success")
    return render_template('admin/login.html', parameter=parameter)


@app.route("/admin/edit-blog/<string:id>",methods=['GET','POST'])
def edit_blog(id):
    if('user' in session and session['user'] == parameter['admin_user']):
        if request.method == 'POST':
            title = request.form.get('title')
            content = request.form.get('content')
            slug = request.form.get('slug')
            img_file = request.form.get('img_file')
            date = datetime.now()
            post = Posts.query.filter_by(id=id).first()
            post.title = title
            post.content = content
            post.slug = slug
            post.img_file = img_file
            post.date = date
            db.session.commit()
            flash("Data Updated Succesfully", "success")
            return redirect('/admin/edit-blog/'+id)
        post = Posts.query.filter_by(id=id).first()
        return render_template('/admin/edit-blog.html', parameter=parameter, post=post)

@app.route("/admin/add-blog/<string:id>",methods=['GET','POST'])
def add_blog(id):
    if('user' in session and session['user'] == parameter['admin_user']):
        if request.method == 'POST':
            title = request.form.get('title')
            content = request.form.get('content')
            slug = request.form.get('slug')
            postedby = request.form.get('posted_by')
            img_file = request.form.get('img_file')
            date = datetime.now()
            if id == '0':
                post = Posts(title=title, content=content, slug=slug, img_file=img_file, date=date, posted_by=postedby)
                db.session.add(post)
                db.session.commit()
            flash("Blog Added Succesfully", "success")
        return render_template('/admin/add-blog.html', parameter=parameter)

@app.route("/admin/logout")
def logout():
    session.pop('user')
    return redirect('/admin/dashboard')

@app.route("/admin/delete/<string:id>", methods=['GET', 'POST'])
def delete(id):
    if ('user' in session and session['user'] == parameter['admin_user']):
        post = Posts.query.filter_by(id=id).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/admin/dashboard')


app.run(debug=True)