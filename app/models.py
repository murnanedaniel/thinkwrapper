from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash # Import hashing functions
from flask_login import UserMixin # Import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True) # Made nullable for now if users can exist before setting a password (e.g. via Paddle first)
    auth0_id = db.Column(db.String(128), nullable=True, index=True)  # Auth0 user ID (like 'auth0|1234567890')
    subscription_id = db.Column(db.String(128), nullable=True, index=True)  # Paddle subscription ID
    is_active = db.Column(db.Boolean, default=True) # General active status
    # paddle_customer_id = db.Column(db.String(128), nullable=True, index=True) # Consider adding later
    # subscription_status = db.Column(db.String(50), nullable=True) # e.g., active, past_due, canceled
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    newsletters = db.relationship("Newsletter", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_or_create_from_auth0(cls, auth0_user):
        """Get existing user or create a new one based on Auth0 user info"""
        user = cls.query.filter_by(auth0_id=auth0_user['sub']).first()
        
        if not user:
            # Create a new user
            user = cls(
                auth0_id=auth0_user['sub'],
                email=auth0_user['email'],
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            
        return user

    def __repr__(self):
        return f'<User {self.email}>'

class Newsletter(db.Model):
    __tablename__ = 'newsletters'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    schedule = db.Column(db.String(50), nullable=True)  # cron expression
    last_sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship("User", back_populates="newsletters")
    issues = db.relationship("Issue", back_populates="newsletter")

class Issue(db.Model):
    __tablename__ = 'issues'
    
    id = db.Column(db.Integer, primary_key=True)
    newsletter_id = db.Column(db.Integer, db.ForeignKey('newsletters.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    newsletter = db.relationship("Newsletter", back_populates="issues") 