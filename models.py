from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tutorials = db.relationship('Tutorial', backref='author', lazy=True)
    progresses = db.relationship('Progress', backref='user', lazy=True)

class Tutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    steps = db.relationship('Step', backref='tutorial', lazy=True)
    progresses = db.relationship('Progress', backref='tutorial', lazy=True)

class Step(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tutorial_id = db.Column(db.Integer, db.ForeignKey('tutorial.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tutorial_id = db.Column(db.Integer, db.ForeignKey('tutorial.id'), nullable=False)
    completed_steps = db.Column(db.Text, default='[]')

    def get_completed_steps(self):
        try:
            return json.loads(self.completed_steps)
        except Exception:
            return []

    def mark_step_complete(self, step_id):
        steps = self.get_completed_steps()
        if step_id not in steps:
            steps.append(step_id)
            self.completed_steps = json.dumps(steps)

    def mark_step_incomplete(self, step_id):
        steps = self.get_completed_steps()
        if step_id in steps:
            steps.remove(step_id)
            self.completed_steps = json.dumps(steps)
