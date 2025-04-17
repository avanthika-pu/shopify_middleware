from flask import Blueprint, request, jsonify
from shopifyapp.services.prompt_service import PromptService
from shopifyapp.models.user import db
from functools import wraps
from flask_login import current_user, login_required

prompt_bp = Blueprint('prompt', __name__)

def store_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        store_id = kwargs.get('store_id') or request.args.get('store_id')
        if not store_id:
            return jsonify({'error': 'Store ID is required'}), 400
        return f(*args, **kwargs)
    return decorated_function

@prompt_bp.route('/api/stores/<int:store_id>/prompts', methods=['GET'])
@login_required
@store_required
def get_prompts(store_id):
    """Get all prompts for a store"""
    return PromptService.get_prompts(store_id, current_user.id)

@prompt_bp.route('/api/stores/<int:store_id>/prompts/<int:prompt_id>', methods=['GET'])
@login_required
@store_required
def get_prompt(store_id, prompt_id):
    """Get a specific prompt"""
    return PromptService.get_prompt(store_id, current_user.id, prompt_id)

@prompt_bp.route('/api/stores/<int:store_id>/prompts', methods=['POST'])
@login_required
@store_required
def create_prompt(store_id):
    """Create a new prompt"""
    prompt_data = request.get_json()
    return PromptService.create_prompt(store_id, current_user.id, prompt_data)

@prompt_bp.route('/api/stores/<int:store_id>/prompts/<int:prompt_id>', methods=['PUT'])
@login_required
@store_required
def update_prompt(store_id, prompt_id):
    """Update a prompt"""
    prompt_data = request.get_json()
    return PromptService.update_prompt(store_id, current_user.id, prompt_id, prompt_data)

@prompt_bp.route('/api/stores/<int:store_id>/prompts/<int:prompt_id>', methods=['DELETE'])
@login_required
@store_required
def delete_prompt(store_id, prompt_id):
    """Delete a prompt"""
    return PromptService.delete_prompt(store_id, current_user.id, prompt_id)

@prompt_bp.route('/api/stores/<int:store_id>/prompt-preferences', methods=['GET'])
@login_required
@store_required
def get_prompt_preferences(store_id):
    """Get prompt preferences for a store"""
    return PromptService.get_prompt_preferences(store_id, current_user.id)

@prompt_bp.route('/api/stores/<int:store_id>/prompt-preferences', methods=['PUT'])
@login_required
@store_required
def update_prompt_preferences(store_id):
    """Update prompt preferences for a store"""
    preferences = request.get_json()
    return PromptService.update_prompt_preferences(store_id, current_user.id, preferences)

@prompt_bp.route('/api/prompt-options', methods=['GET'])
@login_required
def get_prompt_options():
    """Get available options for prompt preferences"""
    return PromptService.get_available_options()

@prompt_bp.route('/api/stores/<int:store_id>/prompts/preview', methods=['POST'])
@login_required
@store_required
def preview_prompt(store_id):
    """Preview a prompt template with sample data"""
    data = request.get_json()
    template = data.get('template')
    context = data.get('context', {})
    
    try:
        rendered = PromptService.render_prompt_preview(template, context)
        return jsonify({'preview': rendered}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400 