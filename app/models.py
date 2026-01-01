from datetime import datetime
from flask_login import UserMixin
from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False)
    google_id = db.Column(db.String(128), unique=True, nullable=True)
    name = db.Column(db.String(100), nullable=True)
    profile_pic = db.Column(db.String(500), nullable=True)
    subscription_id = db.Column(db.String(128), nullable=True)  # Paddle subscription ID
    subscription_status = db.Column(
        db.String(50), default="none"
    )  # none, active, cancelled, past_due
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Cascade behavior: Deleting a user will delete all their newsletters.
    # Since Newsletter also cascades to Issue records, this creates a nested
    # cascade where deleting a user will delete all their newsletters AND all
    # issues associated with those newsletters.
    newsletters = db.relationship(
        "Newsletter", back_populates="user", cascade="all, delete-orphan"
    )


class Newsletter(db.Model):
    __tablename__ = "newsletters"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    schedule = db.Column(db.String(50), nullable=True)  # cron expression
    is_active = db.Column(db.Boolean, default=True)
    last_sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="newsletters")
    issues = db.relationship(
        "Issue", back_populates="newsletter", cascade="all, delete-orphan"
    )


class Issue(db.Model):
    __tablename__ = "issues"

    id = db.Column(db.Integer, primary_key=True)
    newsletter_id = db.Column(
        db.Integer, db.ForeignKey("newsletters.id"), nullable=False
    )
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    newsletter = db.relationship("Newsletter", back_populates="issues")
