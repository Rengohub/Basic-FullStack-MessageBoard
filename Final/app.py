###### Joey Bauer and Zay DeHerrera #######
from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, \
    login_user, logout_user, current_user, login_required
from datetime import datetime, timezone

# Initialize the app and database
app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Creates the users database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    posts = db.relationship('Post', backref='user')

# Creates a post class that links to the user id to track the author as well as when it was posted to help with filtering.
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

with app.app_context():
    db.create_all()

# Initialize the login manager to handle sessions
app.config['SECRET_KEY'] = 'rogerDoger'
login_manager = LoginManager(app)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

# Home page will basically be the landing page
@app.route('/')
def home():
    if current_user.is_authenticated:
        posts = Post.query.all()
        return render_template('home.html', posts=posts)
    else:
        return render_template('home.html')

# Login route to allow existing users access
@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            login_user(user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
    return render_template('login.html', error_message=error_message)

# Logout route to allow signed in users to leave
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# View route to see everyone's post and allow them to edit OWN posts.
@app.route('/addPost', methods=['GET', 'POST'])
@login_required
def addPost():
    if request.method == 'POST':
        post_content = request.form['content']
        new_post = Post(content=post_content, user_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        return redirect('/')
    else:
        return render_template('addPost.html')

# Edit Post Route
@app.route('/editPost/<int:post_id>', methods=['GET', 'POST'])
@login_required
def editPost(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        return redirect('/')
    if request.method == 'POST':
        post.content = request.form['content']
        db.session.commit()
        return redirect('/')
    return render_template('editPost.html', post=post)

# Delete Post route
@app.route('/deletePost/<int:post_id>', methods=['POST'])
@login_required
def deletePost(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        # Redirect or show an error if the current user is not the author
        return redirect('/')
    
    db.session.delete(post)
    db.session.commit()
    return redirect('/')


# Register route to create a unique account
@app.route('/register', methods=['GET', 'POST'])
def register():
    error_message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']
        
        existing_user = User.query.filter_by(username=username).first()
        
        if confirm != password or existing_user:
                error_message = "Invalid username or password"
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
        
            login_user(new_user)
            return redirect('/')
    return render_template('register.html', error_message=error_message)

# Update route to edit the password of the user
@app.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    error_message = None
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        
        if current_user.password == current_password:
            current_user.password = new_password
            db.session.commit()
            return redirect('/')
        else:
            error_message = 'Incorrect current password'
            
    return render_template('update.html', error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)