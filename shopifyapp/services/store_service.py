from flask import current_app, url_for
from typing import Dict, List, Optional, Tuple, Union
from ..models.user import db
from ..models.store import Store
from datetime import datetime
import requests
import hmac
import hashlib
import base64
import os

class StoreService:
    @staticmethod
    def add_store(user_id: int, store_url: str, store_name: Optional[str] = None, 
                  prompt_preferences: Optional[Dict] = None) -> Tuple[Dict, int]:
        """Add a new Shopify store
        
        Args:
            user_id: The ID of the user adding the store
            store_url: The URL of the Shopify store
            store_name: Optional name for the store
            prompt_preferences: Optional dictionary of prompt preferences
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            # Validate and format store URL
            if not store_url.startswith(('http://', 'https://')):
                store_url = f'https://{store_url}'
            
            # Check if store already exists for this user
            existing_store = Store.query.filter_by(
                user_id=user_id,
                store_url=store_url
            ).first()
            
            if existing_store:
                return {'error': 'Store already exists for this user'}, 400

            # Create new store
            store = Store(
                user_id=user_id,
                store_url=store_url,
                store_name=store_name,
                prompt_preferences=prompt_preferences or {}
            )
            
            db.session.add(store)
            db.session.commit()

            # Generate OAuth URL
            oauth_url = StoreService.generate_oauth_url(store)
            
            return {
                'message': 'Store initialization started',
                'store': store.to_dict(),
                'oauth_url': oauth_url
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def get_user_stores(user_id: int) -> Union[Dict[str, List[Dict]], Tuple[Dict[str, str], int]]:
        """Get all stores for a user
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Dictionary containing list of stores or error response tuple
        """
        try:
            stores = Store.query.filter_by(user_id=user_id).all()
            return {'stores': [store.to_dict() for store in stores]}
            
        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def get_store(user_id: int, store_id: int) -> Optional[Dict]:
        """Get specific store details
        
        Args:
            user_id: The ID of the user
            store_id: The ID of the store
            
        Returns:
            Store details dictionary or None if not found
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return None
            return store.to_dict()
            
        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def update_store(user_id: int, store_id: int, store_data: Dict) -> Tuple[Dict, int]:
        """Update store settings
        
        Args:
            user_id: The ID of the user
            store_id: The ID of the store
            store_data: Dictionary containing fields to update
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404
                
            # Update allowed fields
            if 'store_name' in store_data:
                store.store_name = store_data['store_name']
            if 'prompt_preferences' in store_data:
                store.prompt_preferences = store_data['prompt_preferences']
            if 'is_active' in store_data:
                store.is_active = store_data['is_active']
                
            db.session.commit()
            return {'message': 'Store updated successfully', 'store': store.to_dict()}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def delete_store(user_id: int, store_id: int) -> Tuple[Dict, int]:
        """Delete a store
        
        Args:
            user_id: The ID of the user
            store_id: The ID of the store
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404
                
            db.session.delete(store)
            db.session.commit()
            return {'message': 'Store deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def generate_oauth_url(store: Store) -> str:
        """Generate Shopify OAuth URL
        
        Args:
            store: Store model instance
            
        Returns:
            Generated OAuth URL string
        """
        client_id = current_app.config['SHOPIFY_API_KEY']
        redirect_uri = url_for('api.complete_oauth', store_id=store.id, _external=True)
        scopes = store.scopes
        
        # Generate nonce for state parameter
        state = base64.b64encode(os.urandom(16)).decode('utf-8')
        
        oauth_url = (
            f"https://{store.store_url}/admin/oauth/authorize?"
            f"client_id={client_id}&"
            f"scope={scopes}&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}"
        )
        
        return oauth_url

    @staticmethod
    def complete_oauth(user_id: int, store_id: int, code: str) -> Tuple[Dict, int]:
        """Complete Shopify OAuth process
        
        Args:
            user_id: The ID of the user
            store_id: The ID of the store
            code: OAuth authorization code
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            # Exchange code for access token
            client_id = current_app.config['SHOPIFY_API_KEY']
            client_secret = current_app.config['SHOPIFY_API_SECRET']
            
            token_url = f"https://{store.store_url}/admin/oauth/access_token"
            response = requests.post(token_url, json={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code
            })
            
            if response.status_code != 200:
                return {'error': 'Failed to get access token'}, 400
                
            data = response.json()
            store.access_token = data['access_token']
            store.installation_complete = True
            store.last_synced = datetime.utcnow()
            
            # Get store details from Shopify
            headers = {'X-Shopify-Access-Token': store.access_token}
            shop_url = f"https://{store.store_url}/admin/api/{store.api_version}/shop.json"
            shop_response = requests.get(shop_url, headers=headers)
            
            if shop_response.status_code == 200:
                shop_data = shop_response.json()['shop']
                store.shopify_store_id = str(shop_data['id'])
                if not store.store_name:
                    store.store_name = shop_data['name']
            
            db.session.commit()
            
            return {
                'message': 'OAuth completed successfully',
                'store': store.to_dict()
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def verify_webhook(data: bytes, hmac_header: str, webhook_secret: str) -> bool:
        """Verify Shopify webhook signature
        
        Args:
            data: Raw webhook data
            hmac_header: HMAC header from Shopify
            webhook_secret: Webhook secret key
            
        Returns:
            Boolean indicating if signature is valid
        """
        digest = hmac.new(
            webhook_secret.encode('utf-8'),
            data,
            hashlib.sha256
        ).digest()
        computed_hmac = base64.b64encode(digest).decode('utf-8')
        return hmac.compare_digest(computed_hmac, hmac_header) 