from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    channel = db.Column(db.String(100), nullable=False)
    views = db.Column(db.Integer, nullable=False)
    subscribers = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(200), nullable=False)  # URLカラムを追加
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())