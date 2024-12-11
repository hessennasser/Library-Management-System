from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'c4f5e8a3d2b4e7f1b5a9e3b1f4c7d8e9'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    has_library_card = db.Column(db.Boolean, default=False)
    checkouts = db.relationship('Book', backref='current_holder', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create_default_admin():
        # Check if any admin exists
        admin_exists = User.query.filter_by(is_admin=True).first() is not None
        
        if not admin_exists:
            # Create default admin user
            admin = User(
                username='admin',
                is_admin=True,
                has_library_card=True
            )
            admin.set_password('admin123')  # Default password
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created with username: 'admin' and password: 'admin123'")

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    books = db.relationship('Book', backref='author', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    holder_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    checkout_date = db.Column(db.DateTime)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    books = Book.query.all()
    return render_template('home.html', books=books)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Admin routes
@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    books = Book.query.all()
    users = User.query.all()
    return render_template('admin_panel.html', books=books, users=users)

@app.route('/admin/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    if request.method == 'POST':
        title = request.form['title']
        author_name = request.form['author']
        author = Author.query.filter_by(name=author_name).first()
        if not author:
            author = Author(name=author_name)
            db.session.add(author)
        book = Book(title=title, author=author)
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully')
        return redirect(url_for('admin_panel'))
    return render_template('add_book.html')

@app.route('/admin/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        book.title = request.form['title']
        author_name = request.form['author']
        
        # Check if author exists, if not create new one
        author = Author.query.filter_by(name=author_name).first()
        if not author:
            author = Author(name=author_name)
            db.session.add(author)
        
        book.author = author
        db.session.commit()
        flash('Book updated successfully')
        return redirect(url_for('admin_panel'))
    
    return render_template('edit_book.html', book=book)

@app.route('/admin/delete_book/<int:book_id>')
@login_required
def delete_book(book_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully')
    return redirect(url_for('admin_panel'))

@app.route('/admin/issue_card/<int:user_id>')
@login_required
def issue_library_card(user_id):
    if not current_user.is_admin:
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    user.has_library_card = True
    db.session.commit()
    flash('Library card issued successfully')
    return redirect(url_for('admin_panel'))

@app.route('/admin/deactivate_card/<int:user_id>')
@login_required
def deactivate_library_card(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    # Check if user has any books checked out
    if user.checkouts:
        flash('Cannot deactivate card while user has books checked out')
        return redirect(url_for('admin_panel'))
    
    user.has_library_card = False
    db.session.commit()
    flash('Library card deactivated successfully')
    return redirect(url_for('admin_panel'))


# User routes
@app.route('/checkout/<int:book_id>')
@login_required
def checkout_book(book_id):
    if not current_user.has_library_card:
        flash('You need a library card to checkout books')
        return redirect(url_for('home'))
    book = Book.query.get_or_404(book_id)
    if not book.is_available:
        flash('Book is not available')
        return redirect(url_for('home'))
    book.is_available = False
    book.holder_id = current_user.id
    book.checkout_date = datetime.utcnow()
    db.session.commit()
    flash('Book checked out successfully')
    return redirect(url_for('home'))

@app.route('/return/<int:book_id>')
@login_required
def return_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.holder_id != current_user.id:
        flash('This book was not checked out by you')
        return redirect(url_for('home'))
    book.is_available = True
    book.holder_id = None
    book.checkout_date = None
    db.session.commit()
    flash('Book returned successfully')
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        User.create_default_admin()
    app.run(debug=True, port=5001)