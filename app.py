from flask import Flask, request, render_template, redirect, url_for, session
import requests
import os
import json
from datetime import datetime


app = Flask(__name__)
# セッションを安全に保つための秘密鍵。本番環境では推測されにくいランダムな文字列に変更してください。
app.secret_key = os.urandom(24)

# --- Discord OAuth2 設定 ---
# 重要：これらの値は環境変数から読み込むことを強く推奨します。
# 例: client_id = os.getenv('DISCORD_CLIENT_ID')

# リダイレクトURIはDiscordの開発者ポータルで設定したものと完全に一致させる必要があります。
REDIRECT_URI = f'http://localhost:{PORT}/callback'


# APIエンドポイント
API_BASE_URL = 'https://discord.com/api'
AUTHORIZATION_URL = f'{API_BASE_URL}/oauth2/authorize'
TOKEN_URL = f'{API_BASE_URL}/oauth2/token'


# 投稿を保存するファイル
BBS_FILE = 'bbs.json'

# --- データ操作関数 (変更なし) ---
def load_posts():
    if not os.path.exists(BBS_FILE): return []
    try:
        with open(BBS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError): return []

def save_post(new_post):
    posts = load_posts()
    posts.append(new_post)
    with open(BBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=4, ensure_ascii=False)

# --- Flask ルート ---
@app.route('/', methods=['GET', 'POST'])
def bbs():
    """
    BBSのメインページ。
    ログイン状態とサーバー参加状況に応じて、BBS本体かログイン要求ページを表示する。
    """
    # --- 権限チェックを強化 ---
    # セッションにユーザー情報がない、またはサーバーメンバーでない場合はアクセスを拒否
    if 'user' not in session or not session.get('is_member'):
        return render_template('login_required.html', title='閲覧権限がありません')

    # --- 以下はログイン済みかつサーバー参加済みのユーザー向けの処理 ---
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            user_info = session['user']
            avatar_url = f"https://cdn.discordapp.com/avatars/{user_info['id']}/{user_info['avatar']}.png" if user_info.get('avatar') else None
            new_post = {
                'username': user_info['username'],
                'avatar_url': avatar_url,
                'message': message,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            save_post(new_post)
        return redirect(url_for('bbs'))

    posts = load_posts()
    posts.reverse()
    return render_template('bbs.html', title='Server Member BBS', posts=posts)

@app.route('/login')
def login():
    """
    ユーザーをDiscordの認証ページにリダイレクトする。
    'guilds'スコープを追加してサーバー情報を要求する。
    """
    # スコープに 'guilds' を追加
    scope = 'identify%20guilds' # %20 はURLエンコードされたスペース
    discord_auth_url = (
        f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}'
        f'&scope={scope}&redirect_uri={REDIRECT_URI}&prompt=consent'
    )
    return redirect(discord_auth_url)

@app.route('/callback')
def callback():
    """
    Discordからのコールバックを処理し、サーバー参加状況を確認する。
    """
    authorization_code = request.args.get("code")
    if not authorization_code:
        return render_template('error.html', title='Error', message='Authorization code not found.')

    token_data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': REDIRECT_URI,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        # アクセストークンを取得
        token_request = requests.post(TOKEN_URL, data=token_data, headers=headers)
        token_request.raise_for_status()
        access_token = token_request.json()['access_token']

        # --- サーバー参加状況の確認 ---
        auth_headers = {'Authorization': f'Bearer {access_token}'}
        
        # ユーザーの所属サーバー一覧を取得
        guilds_request = requests.get(f'{API_BASE_URL}/users/@me/guilds', headers=auth_headers)
        guilds_request.raise_for_status()
        guilds = guilds_request.json()

        # 指定したサーバーに参加しているかチェック
        is_member = any(g['id'] == GUILD_ID for g in guilds)
        
        if not is_member:
            return render_template('error.html', title='Access Denied', message=f'指定されたサーバーに参加していません。')

        # ユーザー情報を取得
        user_info_request = requests.get(f'{API_BASE_URL}/users/@me', headers=auth_headers)
        user_info_request.raise_for_status()
        user_info = user_info_request.json()

        # セッションにユーザー情報とメンバーフラグを保存
        session['user'] = {
            'id': user_info.get('id'),
            'username': user_info.get('username'),
            'avatar': user_info.get('avatar'),
        }
        session['is_member'] = True
        
        return redirect(url_for('bbs'))

    except requests.exceptions.RequestException as e:
        return render_template('error.html', title='Error', message=f'An API error occurred: {e}')

@app.route('/logout')
def logout():
    """セッションからユーザー情報とメンバーフラグを削除し、ログアウトする"""
    session.pop('user', None)
    session.pop('is_member', None) # メンバーフラグも削除
    return redirect(url_for('bbs'))


if __name__ == "__main__":
    if not os.path.exists(BBS_FILE):
        with open(BBS_FILE, 'w') as f: json.dump([], f)
    app.run(port=PORT, debug=True)