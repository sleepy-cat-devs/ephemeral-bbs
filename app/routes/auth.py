"""Discord認証機能を提供するFlask Blueprintモジュール。

このモジュールは、DiscordのOAuth2認証を通じて、
・ユーザーのログイン
・認可コードのコールバック処理
・ギルド (サーバー) への参加確認
・セッションへのユーザー情報格納
・ログアウト処理
を提供します。

【主なエンドポイント】
 - GET /login     : Discord認証画面へリダイレクト
 - GET /callback  : Discordからの認証情報を処理し、セッションを確立
 - GET /logout    : セッションを破棄しログアウト

【主な関数】
 - login()    : Discordの認証画面へリダイレクト
 - callback() : 認証トークン取得・サーバー所属確認・ユーザー情報取得
 - logout()   : セッション情報のクリアとリダイレクト

【セッション構造】
 - "user": {
      "id": DiscordユーザーID,
      "username": 表示名,
      "avatar": アバターのファイル名
   }
 - "is_member": 対象ギルド参加者であればTrue

【注意点】
 - 認証に失敗した場合、エラーページを表示します。
 - 対象ギルドに参加していないユーザーはアクセス拒否されます。
"""

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
import requests
from werkzeug.wrappers import Response as WerkzeugResponse

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login")
def login() -> WerkzeugResponse:
    """Discordにログインするためのリダイレクトを行います。

    Returns:
        WerkzeugResponse: レスポンスオブジェクト

    """
    return redirect(Const.DISCORD_AUTH_URL)


@auth_bp.route("/callback")
def callback() -> Response | WerkzeugResponse:
    """DiscordのOAuth2認証コールバックを処理します。

    Returns:
        WerkzeugResponse: レスポンスオブジェクト

    """
    authorization_code = request.args.get("code")

    if not authorization_code:
        return Response(
            render_template(
                "error.html",
                title="Error",
                message="Authorization code not found.",
            ),
        )

    token_data = {
        "client_id": Const.CLIENT_ID,
        "client_secret": Const.CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": Const.REDIRECT_URL,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        token_request = requests.post(
            Const.TOKEN_URL,
            data=token_data,
            headers=headers,
            timeout=Const.CONNECT_TIMEOUT,
        )
        token_request.raise_for_status()

        access_token = token_request.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        guilds_request = requests.get(
            f"{Const.API_BASE_URL}/users/@me/guilds",
            headers=auth_headers,
            timeout=Const.CONNECT_TIMEOUT,
        )
        guilds_request.raise_for_status()
        guilds = guilds_request.json()
        is_member = any(g["id"] in Const.GUILD_IDS for g in guilds)
        if not is_member:
            return Response(
                render_template(
                    "error.html",
                    title="Access Denied",
                    message="指定されたサーバーに参加していません。",
                ),
            )
        user_info_request = requests.get(
            f"{Const.API_BASE_URL}/users/@me",
            headers=auth_headers,
            timeout=Const.CONNECT_TIMEOUT,
        )
        user_info_request.raise_for_status()
        user_info = user_info_request.json()
        user_info = user_info_request.json()
        session["user"] = {
            "id": user_info.get("id"),
            "username": user_info.get("username"),
            "avatar": user_info.get("avatar"),
        }
        session["is_member"] = True
        return redirect(url_for("bbs.bbs"))
    except requests.exceptions.RequestException as e:
        return Response(
            render_template(
                "error.html",
                title="Error",
                message=f"An API error occurred: {e}",
            ),
        )


@auth_bp.route("/logout")
def logout() -> Response | WerkzeugResponse:
    """ログアウトする

    Returns:
        Response | WerkzeugResponse: レスポンスオブジェクト

    """
    session.pop("user", None)
    session.pop("is_member", None)
    return redirect(url_for("bbs.bbs"))
