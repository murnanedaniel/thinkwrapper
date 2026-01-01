from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(254), unique=True, nullable=False)
    paddle_customer_id = Column(String(128), nullable=True)  # Paddle customer ID
    subscription_id = Column(String(128), nullable=True)  # Paddle subscription ID
    subscription_status = Column(String(50), nullable=True)  # active, past_due, cancelled, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    newsletters = relationship("Newsletter", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

class Newsletter(Base):
    __tablename__ = 'newsletters'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    topic = Column(String(100), nullable=False)
    schedule = Column(String(50), nullable=True)  # cron expression
    last_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="newsletters")
    issues = relationship("Issue", back_populates="newsletter")

class Issue(Base):
    __tablename__ = 'issues'
    
    id = Column(Integer, primary_key=True)
    newsletter_id = Column(Integer, ForeignKey('newsletters.id'), nullable=False)
    subject = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    newsletter = relationship("Newsletter", back_populates="issues")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    paddle_transaction_id = Column(String(128), unique=True, nullable=False)
    paddle_subscription_id = Column(String(128), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(50), nullable=False)  # completed, pending, failed, refunded
    event_type = Column(String(100), nullable=False)  # subscription.created, transaction.completed, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="transactions") 