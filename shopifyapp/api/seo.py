from flask import Blueprint, jsonify, request
from shopifyapp.services.seo_service import SEOService
from shopifyapp.api.auth import token_required

seo_bp = Blueprint('seo', __name__)

@seo_bp.route('/stores/<int:store_id>/products/<int:product_id>/optimize', methods=['POST'])
@token_required
def optimize_product(current_user, store_id, product_id):
    """Optimize a single product description"""
    data = request.get_json() or {}
    custom_prompt = data.get('custom_prompt')
    
    result, status_code = SEOService.optimize_product_description(
        user_id=current_user.id,
        store_id=store_id,
        product_id=product_id,
        custom_prompt=custom_prompt
    )
    return jsonify(result), status_code

@seo_bp.route('/stores/<int:store_id>/products/optimize-all', methods=['POST'])
@token_required
def optimize_all_products(current_user, store_id):
    """Optimize all product descriptions in a store"""
    data = request.get_json() or {}
    custom_prompt = data.get('custom_prompt')
    
    result, status_code = SEOService.optimize_all_products(
        user_id=current_user.id,
        store_id=store_id,
        custom_prompt=custom_prompt
    )
    return jsonify(result), status_code 