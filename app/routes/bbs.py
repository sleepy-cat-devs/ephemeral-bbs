"""掲示板 (BBS) 機能のルーティングとデータ管理を行うモジュール。

このモジュールはFlaskのBlueprintを用いて、
・掲示板の表示
・投稿データの保存/読み込み
・認証済みユーザーのみのアクセス制御
を提供します。

【主なエンドポイント】
 - GET/POST / : 掲示板の閲覧・投稿

【主な関数】
 - load_posts(): 投稿データの読み込み
 - save_post(): 投稿データの保存

【データ構造】
 - Post: 投稿データの型定義 (ユーザー名・本文・タイムスタンプ)
"""

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import TypedDict

from const import Const
from flask import (
    Blueprint,
    Response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.wrappers import Response as WerkzeugResponse


class Post(TypedDict):
    """掲示板の投稿データ型定義"""

    username: str
    message: str
    timestamp: str


bbs_bp = Blueprint("bbs", __name__)


# --- データ操作関数 ---
def load_posts() -> list[Post]:
    """掲示板の投稿データを読み込みます。

    Returns:
        list[Post]: 読み込んだ投稿データのリスト

    """
    if not Path(Const.BBS_FILE).exists():
        return []
    try:
        with Path(Const.BBS_FILE).open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_post(new_post: Post) -> None:
    """掲示板の投稿データを保存します。

    Args:
        new_post (Post): 保存する投稿データ

    Raises:
        RuntimeError: 投稿データの保存に失敗した場合

    """
    posts = load_posts()
    posts.append(new_post)
    try:
        with Path(Const.BBS_FILE).open("w", encoding="utf-8") as f:
            json.dump(posts, f, indent=4, ensure_ascii=False)
    except Exception as e:
        msg = f"Failed to save post: {e}"
        raise RuntimeError(msg) from e


@bbs_bp.route("/", methods=["GET", "POST"])
def bbs() -> Response | WerkzeugResponse:
    """掲示板の表示と投稿を処理します。

    Returns:
        Response | WerkzeugResponse: レスポンスオブジェクト

    """
    if "user" not in session or not session.get("is_member"):
        return Response(
            render_template("login_required.html", title="閲覧権限がありません"),
        )

    if request.method == "POST":
        message = request.form.get("message")
        if message:
            user_info = session["user"]
            new_post: Post = {
                "username": user_info["username"],
                "message": message,
                "timestamp": datetime.now(tz=UTC).isoformat(),
            }
            try:
                save_post(new_post)
            except RuntimeError as e:
                return Response(
                    render_template(
                        "bbs.html",
                        title="Server Member BBS",
                        posts=load_posts()[::-1],
                        error_message=str(e),
                    ),
                )
        return redirect(url_for("bbs.bbs"))

    posts = load_posts()
    posts.reverse()
    return Response(render_template("bbs.html", title="Server Member BBS", posts=posts))
