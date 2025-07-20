import requests
from flask import Blueprint, redirect, render_template, request, session, url_for

from app.const import Const

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login")
def login():
    return redirect(Const.DISCORD_AUTH_URL)


@auth_bp.route("/callback")
def callback():
    authorization_code = request.args.get("code")

    if not authorization_code:
        return render_template(
            "error.html",
            title="Error",
            message="Authorization code not found.",
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
            timeout=10,
        )
        token_request.raise_for_status()

        access_token = token_request.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        guilds_request = requests.get(
            f"{Const.API_BASE_URL}/users/@me/guilds",
            headers=auth_headers,
            timeout=10,
        )
        guilds_request.raise_for_status()
        guilds = guilds_request.json()
        is_member = any(g["id"] == Const.GUILD_IDS for g in guilds)
        if not is_member:
            return render_template(
                "error.html",
                title="Access Denied",
                message="指定されたサーバーに参加していません。",
            )
        user_info_request = requests.get(
            f"{Const.API_BASE_URL}/users/@me",
            headers=auth_headers,
            timeout=10,
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
        return render_template(
            "error.html",
            title="Error",
            message=f"An API error occurred: {e}",
        )


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("is_member", None)
    return redirect(url_for("bbs.bbs"))
