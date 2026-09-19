from api.database import db

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chat.id"))
    role = db.Column(db.String(20))
    content = db.Column(db.Text)