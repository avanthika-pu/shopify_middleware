from flask import Blueprint, jsonify, request
from shopifyapp.services.prompt_service import PromptService
from shopifyapp.api.auth import token_required

prompt_bp = Blueprint('prompt', __name__)

@prompt_bp.route('/stores/<int:store_id>/prompts/preferences', methods=['GET'])
@token_required
def get_prompt_preferences(current_user, store_id):
    """Get prompt preferences for a store"""
    result, status_code = PromptService.get_prompt_preferences(
        store_id=store_id,
        user_id=current_user.id
    )
    return jsonify(result), status_code

@prompt_bp.route('/stores/<int:store_id>/prompts/preferences', methods=['PUT'])
@token_required
def update_prompt_preferences(current_user, store_id):
    """Update prompt preferences for a store"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    result, status_code = PromptService.update_prompt_preferences(
        store_id=store_id,
        user_id=current_user.id,
        preferences=data
    )
    return jsonify(result), status_code

@prompt_bp.route('/prompts/options', methods=['GET'])
@token_required
def get_available_options():
    """Get available options for prompt preferences"""
    return jsonify(PromptService.get_available_options()), 200 