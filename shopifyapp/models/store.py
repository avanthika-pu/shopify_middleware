from datetime import datetime
from .user import db

class Store(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    store_url = db.Column(db.String(255), nullable=False)
    store_name = db.Column(db.String(100))
    access_token = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    last_synced = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Shopify specific fields
    shopify_store_id = db.Column(db.String(100))
    api_version = db.Column(db.String(20), default='2024-01')
    webhook_secret = db.Column(db.String(255))
    scopes = db.Column(db.String(500), default='read_products,write_products')
    installation_complete = db.Column(db.Boolean, default=False)

    # Prompt preferences with detailed structure
    prompt_preferences = db.Column(db.JSON, default={
        'tone': 'professional',
        'target_audience': 'general',
        'writing_style': 'descriptive',
        'seo_keywords_focus': 'balanced',
        'description_length': 'medium',
        'key_features': [],
        'brand_voice': {
            'personality': 'professional',
            'emotion': 'neutral',
            'formality': 'formal'
        },
        'industry_specific': {
            'industry': None,
            'specializations': [],
            'technical_level': 'moderate'
        },
        'custom_instructions': '',
        'example_description': '',
        'avoid_words': [],
        'must_include_elements': [],
        'template_sections': [
            'introduction',
            'key_features',
            'benefits',
            'specifications',
            'call_to_action'
        ]
    })

    # Relationships
    products = db.relationship('Product', back_populates='store', cascade='all, delete-orphan')
    prompts = db.relationship('Prompt', back_populates='store', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'store_url': self.store_url,
            'store_name': self.store_name,
            'is_active': self.is_active,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None,
            'prompt_preferences': self.prompt_preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'has_access_token': bool(self.access_token),
            'installation_complete': self.installation_complete,
            'api_version': self.api_version,
            'scopes': self.scopes.split(',') if self.scopes else []
        }

    def get_admin_url(self):
        """Get the Shopify admin URL for this store"""
        if not self.store_url:
            return None
        return f"https://{self.store_url.replace('https://', '').replace('http://', '')}/admin"

    def get_api_url(self):
        """Get the Shopify API URL for this store"""
        if not self.store_url:
            return None
        return f"https://{self.store_url.replace('https://', '').replace('http://', '')}/admin/api/{self.api_version}" 