import os
import secrets
from flask import Flask, render_template, url_for, flash, redirect, request, abort
from flask1.logforms import RegistrationForm, LoginForm, UpdateForm, PostForm, ResetRequestForm, ResetPasswordForm
from flask1.models import Post, User
from flask1 import app, db, bcrypt, mail
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

db.create_all()



@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    info = Post.query.order_by(Post.year.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', info=info, title='home')


@app.route('/about')
def about():
    return render_template('about.html', title='trying 1')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hash_pass = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data,password=hash_pass)
        db.session.add(user)
        db.session.commit()
        flash(f'Account Created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
       user = User.query.filter_by(email=form.email.data).first()
       if user and bcrypt.check_password_hash(user.password, form.password.data):
           login_user(user, remember=form.remember.data)
           next_page = request.args.get('next')
           if next_page:
               return redirect(next_page)
           return redirect(url_for('home'))
       flash('please enter valid account details', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

def save_picture(user_pic):
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(user_pic.filename)
    picture_fn = random_hex + file_ext
    picture_path = os.path.join(app.root_path, 'static','profile', picture_fn)
    user_pic.save(picture_path)
    return picture_fn


@app.route('/account', methods=['Get', 'POST'])
@login_required
def account():
    form = UpdateForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account Updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile/' + current_user.image)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, information=form.information.data, name=current_user.username, admin=current_user, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash("New post created!",'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', legend='New Post', form=form)


@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html',post=post, post_id=post_id)


@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.admin != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.information = form.information.data
        db.session.commit()
        flash('Post updated!', "success")
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.information.data = post.information
    return render_template('create_post.html', title='Update Post', legend='Update Post', form=form)


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.admin != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Post Deleted!', "success")
    return redirect(url_for('home'))
    

@app.route('/user/<username>')
def user_page(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    info = Post.query.filter_by(admin=user).order_by(Post.year.desc()).paginate(page=page, per_page=5)
    return render_template('user_posts.html', info=info, title=user.username, user=user)


def send_reset_token(user):
    token = user.get_request_token()
    msg = Message('Password Reset Request', sender='andrewmartinsergent69@gmail.com', recipients=[user.email])
    msg.body = f'''To reset password visit the following link:
{url_for('reset_password', token=token, _external=True)} 

If you have not made the request then ignore the message.
'''
    mail.send(msg)

@app.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = ResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_token(user)
        flash('check your mail for conformation link....', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route('/reset_request/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_request_token(token)
    if not user:
        flash('Invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_pass = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_pass
        db.session.commit()
        flash('Your pass word has been changed!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title='Reset Password', form=form)
