from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, user_id, email, first_name, last_name, role):
        self.id = user_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.role = role