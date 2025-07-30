from flask import Flask, redirect, url_for, session, request,render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
import datetime
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'dummy_secret_key'  # セッション用

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# メール設定（Gmail用サンプル。パスワードはご自身で設定してください）
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'Seikei.digital@gmail.com'
app.config['MAIL_PASSWORD'] = 'wswj vmpq ljvk xlpa'
app.config['MAIL_DEFAULT_SENDER'] = 'Seikei.digital@gmail.com'

mail = Mail(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    gender = db.Column(db.String(10))
    age_group = db.Column(db.String(10))
    role = db.Column(db.String(10), default='user')
    age = db.Column(db.Integer)  # ←これを復活


# Magic Link用トークン管理モデル
class MagicLinkToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(256), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

serializer = URLSafeTimedSerializer(app.secret_key)

def send_magic_link_email(email, token):
    magic_link = url_for('register_complete', token=token, _external=True)
    subject = "【認証】新規登録用リンクのお知らせ"
    body = f"""
    以下のリンクをクリックして本登録を完了してください（10分間有効です）:

    {magic_link}

    ※このメールに心当たりがない場合は破棄してください。
    """
    msg = Message(subject=subject, recipients=[email], body=body)
    mail.send(msg)

# --- Magic Link関連のコードを全て削除 ---
# DB初期化用
with app.app_context():
    db.create_all()

# send_magic_link, magic_login, MagicLinkToken, serializer, send_magic_link_email などの定義・利用箇所を削除

@app.route('/')
def cm():
    return render_template('cm.html')



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

@app.route('/debug')
def debug():
    return f"Session: {dict(session)}"


@app.route('/point')
def point():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    email = session.get('email', '')
    role = session.get('role', 'user')
    return render_template('point_get.html', email=email, role=role)

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

# send_magic_link, magic_login, MagicLinkToken, serializer, send_magic_link_email などの定義・利用箇所を削除

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            message = 'メールアドレスを入力してください。'
            return render_template('register.html', message=message)
        # トークン生成
        token = serializer.dumps(email, salt='magic-link')
        # DB保存（同じメールの古いトークンは削除）
        MagicLinkToken.query.filter_by(email=email).delete()
        db.session.add(MagicLinkToken(email=email, token=token))
        db.session.commit()
        # メール送信
        send_magic_link_email(email, token)
        message = '認証用リンクをメールアドレス宛に送信しました。メールをご確認ください。'
        return render_template('register.html', message=message)
    return render_template('register.html', message=message)

@app.route('/register/complete/<token>', methods=['GET', 'POST'])
def register_complete(token):
    message = ''
    try:
        email = serializer.loads(token, salt='magic-link', max_age=600)  # 10分有効
    except Exception:
        message = 'リンクが無効または期限切れです。再度お試しください。'
        return render_template('register_complete.html', message=message)
    # トークンがDBに存在するか確認
    token_entry = MagicLinkToken.query.filter_by(token=token).first()
    if not token_entry:
        message = 'このリンクは既に使用済みか無効です。'
        return render_template('register_complete.html', message=message)
    if request.method == 'POST':
        password = request.form.get('password')
        gender = request.form.get('gender')
        age_group = request.form.get('age_group')
        age = request.form.get('age')
        if User.query.filter_by(email=email).first():
            message = 'このメールアドレスは既に登録されています。'
        else:
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(password)
            user = User(
                email=email,
                password_hash=password_hash,
                gender=gender,
                age_group=age_group,
                age=age
            )
            db.session.add(user)
            db.session.delete(token_entry)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register_complete.html', message=message, email=email)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET'])
def admin_page():
    if session.get('role') not in ['admin', 'super_admin']: 
        return "権限がありません", 403
    users = User.query.all()
    return render_template('admin.html', email=session.get('email', ''), users=users)

@app.route('/admin/update_role', methods=['POST'])
def update_role():
    if session.get('role') != 'super_admin':
        return "権限がありません", 403

    user_id = request.form.get('user_id')
    new_role = request.form.get('role')
    user = User.query.get(user_id)

    if not user or new_role not in ['user', 'admin', 'super_admin']:
        return 'error', 400

    # 自分自身のロールは変更できないようにする
    if user.email == session.get('email'):
        return 'error', 400

    user.role = new_role
    db.session.commit()
    return 'success'


if __name__ == '__main__':
    app.run(debug=True)
