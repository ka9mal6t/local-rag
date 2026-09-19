from api.database import db

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.Text)