from flask import Flask, redirect, url_for, session, request,render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'dummy_secret_key'  # セッション用

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    gender = db.Column(db.String(10))
    age_group = db.Column(db.String(10))

# DB初期化用
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['logged_in'] = True
            session['gender'] = user.gender
            session['age_group'] = user.age_group
            session['email'] = user.email
            session['role'] = getattr(user, 'role', 'user')
            # after_login_redirectがあれば優先
            redirect_target = session.pop('after_login_redirect', None)
            if redirect_target == 'street_stamp':
                return redirect(url_for('street_qr'))
            elif redirect_target == 'shop_stamp':
                return redirect(url_for('shop_qr'))
            return redirect(url_for('home'))
        else:
            message = 'メールアドレスまたはパスワードが正しくありません。'
    return render_template('login.html', message=message)

@app.route('/home')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/bingo')
def bingo():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('bingo.html')

@app.route('/point')
def point():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('point_get.html')

@app.route('/street_qr')
def street_qr():
    if not session.get('logged_in'):
        session['after_login_redirect'] = 'street_stamp'
        return redirect(url_for('login'))
    return render_template('street_stamp.html')

@app.route('/shop_qr')
def shop_qr():
    if not session.get('logged_in'):
        session['after_login_redirect'] = 'shop_stamp'
        return redirect(url_for('login'))
    return render_template('shop_stamp.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        gender = request.form.get('gender')
        age_group = request.form.get('age_group')
        # メール重複チェック
        if User.query.filter_by(email=email).first():
            message = 'このメールアドレスは既に登録されています。'
        else:
            user = User(
                email=email,
                password_hash=generate_password_hash(password),
                gender=gender,
                age_group=age_group
            )
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html', message=message)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
