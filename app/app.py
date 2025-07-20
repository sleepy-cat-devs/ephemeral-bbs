"""エフェメラルBBS Flaskアプリのメインエントリーポイントです"""

import json
import os
from pathlib import Path

from flask import Flask

from app.const import Const
from app.routes.auth import auth_bp
from app.routes.bbs import bbs_bp

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Blueprint登録
app.register_blueprint(bbs_bp)
app.register_blueprint(auth_bp)

if not Path(Const.BBS_FILE).exists():
    with Path(Const.BBS_FILE).open("w") as f:
        json.dump([], f)

app.run(port=Const.PORT, debug=Const.IS_DEBUG)
