from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    company_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    is_email_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Shopify specific fields
    default_prompt_template = db.Column(db.Text)
    prompt_preferences = db.Column(db.JSON, default={})
    api_usage_count = db.Column(db.Integer, default=0)
    subscription_status = db.Column(db.String(20), default='free')
    subscription_expiry = db.Column(db.DateTime)

    # Relationships
    stores = db.relationship('Store', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        """Set the user's password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()

    def increment_api_usage(self):
        self.api_usage_count += 1
        db.session.commit()

    def to_dict(self) -> dict:
        """Convert user object to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'company_name': self.company_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_email_verified': self.is_email_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'api_usage_count': self.api_usage_count,
            'subscription_status': self.subscription_status,
            'subscription_expiry': self.subscription_expiry.isoformat() if self.subscription_expiry else None,
            'has_default_prompt': bool(self.default_prompt_template)
        } 