from datetime import datetime
from ..models.user import db

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    shopify_product_id = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    optimized_description = db.Column(db.Text)
    handle = db.Column(db.String(255))
    vendor = db.Column(db.String(255))
    product_type = db.Column(db.String(255))
    tags = db.Column(db.JSON)
    variants = db.Column(db.JSON)
    images = db.Column(db.JSON)
    status = db.Column(db.String(50), default='pending')  # pending, optimizing, optimized, deployed
    last_synced = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    store = db.relationship('Store', back_populates='products')

    def to_dict(self) -> dict:
        """Convert product object to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'shopify_product_id': self.shopify_product_id,
            'title': self.title,
            'description': self.description,
            'optimized_description': self.optimized_description,
            'handle': self.handle,
            'vendor': self.vendor,
            'product_type': self.product_type,
            'tags': self.tags,
            'variants': self.variants,
            'images': self.images,
            'status': self.status,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 