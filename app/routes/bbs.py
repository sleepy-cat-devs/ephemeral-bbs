import json
import os
from datetime import datetime

from flask import Blueprint, redirect, render_template, request, session, url_for

from app.const import Const

bbs_bp = Blueprint("bbs", __name__)


# --- データ操作関数 ---
def load_posts():
    if not os.path.exists(Const.BBS_FILE):
        return []
    try:
        with open(Const.BBS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_post(new_post):
    posts = load_posts()
    posts.append(new_post)
    with open(Const.BBS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=4, ensure_ascii=False)


@bbs_bp.route("/", methods=["GET", "POST"])
def bbs():
    if "user" not in session or not session.get("is_member"):
        return render_template("login_required.html", title="閲覧権限がありません")

    if request.method == "POST":
        message = request.form.get("message")
        if message:
            user_info = session["user"]
            avatar_url = (
                f"https://cdn.discordapp.com/avatars/{user_info['id']}/{user_info['avatar']}.png"
                if user_info.get("avatar")
                else None
            )
            new_post = {
                "username": user_info["username"],
                "avatar_url": avatar_url,
                "message": message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            save_post(new_post)
        return redirect(url_for("bbs.bbs"))

    posts = load_posts()
    posts.reverse()
    return render_template("bbs.html", title="Server Member BBS", posts=posts)
