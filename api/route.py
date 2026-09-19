from flask import Blueprint, render_template
from api.routes.ask import ask
from api.routes.ask_pdf import ask_pdf
from api.routes.chat import chat
from api.routes.chat_pdf import chat_pdf
from api.routes.upload_pdf import upload_pdf


main = Blueprint("main", __name__, url_prefix="/ai")

@main.route("/")
def index():
    return render_template("chat.html")

main.register_blueprint(ask)
main.register_blueprint(ask_pdf)
main.register_blueprint(chat)
main.register_blueprint(chat_pdf)
main.register_blueprint(upload_pdf)