from .user import User, db
from .store import Store
from .product import Product

__all__ = ['User', 'Store', 'db']

# Set up relationships after all models are defined
def setup_relationships():
    # User relationships
    User.stores = db.relationship('Store', back_populates='user', lazy=True)

    # Store relationships
    Store.user = db.relationship('User', back_populates='stores')
    Store.products = db.relationship('Product', back_populates='store', lazy=True, cascade='all, delete-orphan')

    # Product relationships
    Product.store = db.relationship('Store', back_populates='products') 