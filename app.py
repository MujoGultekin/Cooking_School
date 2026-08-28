import os
from flask import Flask
from flask_login import LoginManager

from config import SECRET_KEY
from dao.user_dao import get_user_by_id
from models import User

from routes.auth_routes import auth_bp
from routes.home_routes import home_bp
from routes.manager_routes import manager_bp
from routes.student_routes import student_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "danger"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    row = get_user_by_id(user_id)
    if row:
        return User(
            user_id=row["id"],
            email=row["email"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            role=row["role"]
        )
    return None


# Blueprint Kayıtları
app.register_blueprint(home_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(manager_bp)
app.register_blueprint(student_bp)

if __name__ == "__main__":
    app.run(debug=True)