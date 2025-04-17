from flask import Blueprint, request, jsonify
from ..services.product_service import ProductService
from .auth import token_required
from ..services.auth_service import auth_required

product_bp = Blueprint('product', __name__)

@product_bp.route('/stores/<int:store_id>/products', methods=['GET'])
@auth_required
def get_store_products(current_user, store_id):
    """Get all products for a specific store"""
    result, status_code = ProductService.get_store_products(store_id, current_user.id)
    return jsonify(result), status_code

@product_bp.route('/products', methods=['GET'])
@auth_required
def get_all_products(current_user):
    """Get all products from all stores for the current user"""
    result, status_code = ProductService.get_all_user_products(current_user.id)
    return jsonify(result), status_code

@product_bp.route('/stores/<int:store_id>/products/<int:product_id>', methods=['GET'])
@auth_required
def get_product(current_user, store_id, product_id):
    """Get a specific product"""
    result, status_code = ProductService.get_product(product_id, store_id, current_user.id)
    return jsonify(result), status_code

@product_bp.route('/stores/<int:store_id>/products/<int:product_id>/optimize', methods=['POST'])
@auth_required
def optimize_product(current_user, store_id, product_id):
    """Optimize a single product description"""
    data = request.get_json() or {}
    custom_prompt = data.get('custom_prompt')
    
    result, status_code = ProductService.optimize_product_description(
        user_id=current_user.id,
        store_id=store_id,
        product_id=product_id,
        custom_prompt=custom_prompt
    )
    return jsonify(result), status_code

@product_bp.route('/stores/<int:store_id>/products/optimize-all', methods=['POST'])
@auth_required
def optimize_all_products(current_user, store_id):
    """Optimize all product descriptions in a store"""
    data = request.get_json() or {}
    custom_prompt = data.get('custom_prompt')
    
    result, status_code = ProductService.optimize_all_products(
        user_id=current_user.id,
        store_id=store_id,
        custom_prompt=custom_prompt
    )
    return jsonify(result), status_code

@product_bp.route('/stores/<int:store_id>/products/<int:product_id>/deploy', methods=['POST'])
@token_required
def deploy_optimization(current_user, store_id, product_id):
    """Deploy optimized description to Shopify store"""
    response, status_code = ProductService.deploy_optimization(
        user_id=current_user.id,
        store_id=store_id,
        product_id=product_id
    )
    return jsonify(response), status_code

@product_bp.route('/stores/<int:store_id>/products/deploy-all', methods=['POST'])
@token_required
def deploy_all_optimizations(current_user, store_id):
    """Deploy all optimized descriptions to Shopify store"""
    response = ProductService.deploy_all_optimizations(
        user_id=current_user.id,
        store_id=store_id
    )
    return jsonify(response), 202  # Accepted, will be processed asynchronously

@product_bp.route('/stores/<int:store_id>/prompt', methods=['PUT'])
@token_required
def update_store_prompt(current_user, store_id):
    """Update store's default prompt template"""
    data = request.get_json()
    if not data or 'prompt_template' not in data:
        return jsonify({'error': 'Prompt template is required'}), 400
        
    response, status_code = ProductService.update_store_prompt(
        user_id=current_user.id,
        store_id=store_id,
        prompt_template=data['prompt_template']
    )
    return jsonify(response), status_code

@product_bp.route('/stores/<int:store_id>/products', methods=['POST'])
@auth_required
def create_product(current_user, store_id):
    """Create a new product in Shopify"""
    data = request.get_json()
    
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
        
    result, status_code = ProductService.create_product(
        store_id=store_id,
        user_id=current_user.id,
        product_data=data
    )
    return jsonify(result), status_code 