import werkzeug.security
from flask import Flask, render_template, redirect, url_for, flash,abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm,Registerform,Login,show
from flask_gravatar import Gravatar
from functools import wraps
import config


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SECRET_KEY'] = config.api_key
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager=LoginManager()
login_manager.init_app(app)


##CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    #This will act like a List of BlogPost objects attached to each User.
    #The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")
    commen=relationship("Comments",back_populates="comme")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # ***************Parent Relationship*************#
    comments = relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    # ***************Child Relationship*************#
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text = db.Column(db.Text, nullable=False)


db.create_all()




@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts,current_user=current_user)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if(current_user.id != 1):
            return abort("403")
        return f(*args,**kwargs)
    return decorated_function


@app.route('/register',methods=["POST","GET"])
def register():
    form1=Registerform()
    if(form1.validate_on_submit()):
        email=form1.email.data
        password=form1.password.data
        name=form1.name.data
        if(User.query.filter_by(email=email).first()):
            flash("Email Is Already There")
            return redirect(url_for("login"))
        else:
            r_user = User(email=email, name=name,
                          password=werkzeug.security.generate_password_hash(password, method="pbkdf2:sha256",
                                                                            salt_length=8))
            db.session.add(r_user)
            db.session.commit()
            login_user(r_user)
        return redirect(url_for("get_all_posts"))


    return render_template("register.html",form=form1)


@app.route('/login',methods=["POST","GET"])
def login():
    form1=Login()
    if(form1.validate_on_submit()):
        email=form1.email.data
        password=form1.password.data
        use=User.query.filter_by(email=email).first()
        if(use):
            if(werkzeug.security.check_password_hash(use.password,password)):
                login_user(use)
                return redirect(url_for("get_all_posts"))
            else:
                flash("The Password That you entered it wrong")
                return redirect(url_for("login"))
        else:
            flash("Please Check Your Email Address")
            return redirect(url_for("login"))
    return render_template("login.html",form=form1)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>")
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    post=show()
    return render_template("post.html", post=requested_post,form=post)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post")
@login_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>")
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000,debug=True)
