"""このモジュールは、アプリケーション全体で使用される定数および設定値を定義します。

環境変数から各種設定値を取得し、アプリケーション内で一貫して利用できるようにします。
"""

import os
from typing import Final


class Const:
    """共通定数"""

    # --- アプリケーション設定 ---
    IS_DEBUG: Final[bool] = os.getenv("ENV") == "dev"
    PORT: Final[int] = int(os.getenv("PORT", "5000"))
    BBS_FILE: Final[str] = os.getenv("BBS_FILE", "bbs.json")
    CONNECT_TIMEOUT: Final[int] = 10  # API接続タイムアウト

    # --- Discord OAuth2 認証関連 ---
    CLIENT_ID: Final[str] = os.getenv("DISCORD_CLIENT_ID", "")
    CLIENT_SECRET: Final[str] = os.getenv("DISCORD_CLIENT_SECRET", "")
    GUILD_IDS: Final[list[str]] = os.getenv("DISCORD_GUILD_ID", "").split(",")
    REDIRECT_URL: Final[str] = os.getenv(
        "REDIRECT_URL",
        f"http://localhost:{PORT}/callback",
    )

    API_BASE_URL: Final[str] = "https://discord.com/api"
    AUTHORIZATION_URL: Final[str] = f"{API_BASE_URL}/oauth2/authorize"
    TOKEN_URL: Final[str] = f"{API_BASE_URL}/oauth2/token"

    _scopes: Final[list[str]] = ["identify", "guilds"]
    # スコープをスペースで結合
    _joined_scope: Final[str] = "%20".join(_scopes)

    # Discord認証URL
    DISCORD_AUTH_URL: Final[str] = (
        f"{AUTHORIZATION_URL}"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        f"&scope={_joined_scope}"
        f"&prompt=consent"
        f"&response_type=code"
    )
