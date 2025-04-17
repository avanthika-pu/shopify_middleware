from flask import Blueprint, request, jsonify, current_app
from shopifyapp.services.store_service import StoreService
from shopifyapp.api.auth import token_required
from ..models.store import Store

store_bp = Blueprint('api', __name__)

@store_bp.route('/stores', methods=['POST'])
@token_required
def add_store(current_user):
    """Add a new Shopify store"""
    data = request.get_json()
    
    if not data or 'store_url' not in data:
        return jsonify({'error': 'store_url is required'}), 400
        
    result, status_code = StoreService.add_store(
        user_id=current_user.id,
        store_url=data['store_url'],
        store_name=data.get('store_name'),
        prompt_preferences=data.get('prompt_preferences')
    )
    
    return jsonify(result), status_code

@store_bp.route('/stores', methods=['GET'])
@token_required
def get_stores(current_user):
    """Get all stores for the current user"""
    result = StoreService.get_user_stores(current_user.id)
    return jsonify(result)

@store_bp.route('/stores/<int:store_id>', methods=['GET'])
@token_required
def get_store(current_user, store_id):
    """Get specific store details"""
    store = StoreService.get_store(current_user.id, store_id)
    if not store:
        return jsonify({'error': 'Store not found'}), 404
    return jsonify(store)

@store_bp.route('/stores/<int:store_id>', methods=['PUT'])
@token_required
def update_store(current_user, store_id):
    """Update store settings"""
    data = request.get_json()
    result, status_code = StoreService.update_store(current_user.id, store_id, data)
    return jsonify(result), status_code

@store_bp.route('/stores/<int:store_id>', methods=['DELETE'])
@token_required
def delete_store(current_user, store_id):
    """Delete a store"""
    result, status_code = StoreService.delete_store(current_user.id, store_id)
    return jsonify(result), status_code

@store_bp.route('/stores/<int:store_id>/auth', methods=['GET'])
@token_required
def complete_oauth(current_user, store_id):
    """Complete Shopify OAuth process"""
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Authorization code is required'}), 400
        
    result, status_code = StoreService.complete_oauth(current_user.id, store_id, code)
    return jsonify(result), status_code

@store_bp.route('/stores/<int:store_id>/webhook', methods=['POST'])
def handle_webhook(store_id):
    """Handle Shopify webhooks"""
    store = Store.query.get_or_404(store_id)
    
    # Verify webhook signature
    hmac_header = request.headers.get('X-Shopify-Hmac-SHA256')
    if not hmac_header:
        return jsonify({'error': 'Missing HMAC header'}), 401
        
    data = request.get_data()
    if not StoreService.verify_webhook(data, hmac_header, store.webhook_secret):
        return jsonify({'error': 'Invalid webhook signature'}), 401
    
    # Process webhook based on type
    webhook_type = request.headers.get('X-Shopify-Topic')
    
    # TODO: Implement webhook handling logic based on type
    # For now, just acknowledge receipt
    return jsonify({'message': f'Webhook received: {webhook_type}'}), 200 