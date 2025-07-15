from flask import Flask, redirect, url_for, session, request

app = Flask(__name__)
app.secret_key = 'dummy_secret_key'  # セッション用

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # ダミーログイン（何も入力せず通過）
        session['logged_in'] = True
        return redirect(url_for('home'))
    return '''
        <form method="post">
            <button type="submit">ログイン</button>
        </form>
    '''

@app.route('/home')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return '''
        <h1>Home画面</h1>
        <a href="/bingo">ビンゴ画面へ</a><br>
        <a href="/point">ポイント使用画面へ</a>
    '''

@app.route('/bingo')
def bingo():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return '<h1>ビンゴ画面</h1><a href="/home">Homeへ戻る</a>'

@app.route('/point')
def point():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return '<h1>ポイント使用画面</h1><a href="/home">Homeへ戻る</a>'

if __name__ == '__main__':
    app.run(debug=True)
