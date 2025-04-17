from flask import current_app
from shopifyapp.models.store import Store
from shopifyapp.models.prompt import Prompt
from shopifyapp.models.user import db
from datetime import datetime
import jinja2
from typing import Dict, List, Optional, Tuple, Union, Any

class PromptService:
    @staticmethod
    def get_prompt_preferences(store_id: int, user_id: int) -> Tuple[Dict[str, Any], int]:
        """
        Get prompt preferences for a store.

        Parameters:
            store_id: ID of the store
            user_id: ID of the store owner

        Returns:
            tuple: (response_dict, status_code)
                response_dict: Contains prompt preferences or error
                status_code: 200 for success, 404 for not found
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404
            
            return {'prompt_preferences': store.prompt_preferences}, 200
        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def update_prompt_preferences(store_id: int, user_id: int, preferences: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Update prompt preferences for a store.

        Parameters:
            store_id: ID of the store
            user_id: ID of the store owner
            preferences: New preferences including tone, style, etc.

        Returns:
            tuple: (response_dict, status_code)
                response_dict: Contains success message and updated preferences
                status_code: 200 for success, 404/400 for errors

        Raises:
            Exception: If update fails
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            # Validate required fields
            required_fields = ['tone', 'target_audience', 'writing_style']
            for field in required_fields:
                if field not in preferences:
                    return {'error': f'Missing required field: {field}'}, 400

            # Update only valid fields
            valid_fields = [
                'tone', 'target_audience', 'writing_style', 'seo_keywords_focus',
                'description_length', 'key_features', 'brand_voice', 'industry_specific',
                'custom_instructions', 'example_description', 'avoid_words',
                'must_include_elements', 'template_sections'
            ]

            # Merge existing preferences with new ones
            updated_preferences = store.prompt_preferences.copy() if store.prompt_preferences else {}
            for field in valid_fields:
                if field in preferences:
                    if field in ['brand_voice', 'industry_specific'] and isinstance(preferences[field], dict):
                        if field not in updated_preferences:
                            updated_preferences[field] = {}
                        updated_preferences[field].update(preferences[field])
                    else:
                        updated_preferences[field] = preferences[field]

            store.prompt_preferences = updated_preferences
            store.updated_at = datetime.utcnow()
            db.session.commit()

            return {
                'message': 'Prompt preferences updated successfully',
                'prompt_preferences': store.prompt_preferences
            }, 200

        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def get_prompts(store_id: int, user_id: int) -> Tuple[Dict[str, Union[str, List[Dict[str, Any]]]], int]:
        """
        Get all prompts for a store.

        Parameters:
            store_id: ID of the store
            user_id: ID of the store owner

        Returns:
            tuple: (response_dict, status_code)
                response_dict: Contains list of prompts or error
                status_code: 200 for success, 404 for not found
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            prompts = Prompt.query.filter_by(store_id=store_id).all()
            return {'prompts': [prompt.to_dict() for prompt in prompts]}, 200
        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def get_prompt(store_id: int, user_id: int, prompt_id: int) -> Tuple[Dict[str, Any], int]:
        """
        Get a specific prompt.

        Parameters:
            store_id: ID of the store
            user_id: ID of the store owner
            prompt_id: ID of the prompt to retrieve

        Returns:
            tuple: (response_dict, status_code)
                response_dict: Contains prompt data or error
                status_code: 200 for success, 404 for not found
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            prompt = Prompt.query.filter_by(id=prompt_id, store_id=store_id).first()
            if not prompt:
                return {'error': 'Prompt not found'}, 404

            return {'prompt': prompt.to_dict()}, 200
        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def create_prompt(store_id: int, user_id: int, prompt_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Create a new prompt.

        Parameters:
            store_id: ID of the store
            user_id: ID of the store owner
            prompt_data: Prompt details including name, template, etc.

        Returns:
            tuple: (response_dict, status_code)
                response_dict: Contains success message and created prompt
                status_code: 201 for created, 404/400 for errors

        Raises:
            Exception: If creation fails or template syntax is invalid
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            # Validate required fields
            required_fields = ['name', 'template']
            for field in required_fields:
                if field not in prompt_data:
                    return {'error': f'Missing required field: {field}'}, 400

            # Validate template syntax
            try:
                jinja2.Template(prompt_data['template'])
            except Exception as e:
                return {'error': f'Invalid template syntax: {str(e)}'}, 400

            # Create new prompt
            prompt = Prompt(
                store_id=store_id,
                name=prompt_data['name'],
                description=prompt_data.get('description'),
                template=prompt_data['template'],
                is_default=prompt_data.get('is_default', False),
                is_active=prompt_data.get('is_active', True),
                variables=prompt_data.get('variables', {}),
                tone=prompt_data.get('tone', 'professional'),
                target_audience=prompt_data.get('target_audience', 'general'),
                writing_style=prompt_data.get('writing_style', 'descriptive'),
                seo_keywords_focus=prompt_data.get('seo_keywords_focus', 'balanced'),
                description_length=prompt_data.get('description_length', 'medium'),
                key_features=prompt_data.get('key_features', []),
                brand_voice=prompt_data.get('brand_voice', {
                    'personality': 'professional',
                    'emotion': 'neutral',
                    'formality': 'formal'
                }),
                industry_specific=prompt_data.get('industry_specific', {
                    'industry': None,
                    'specializations': [],
                    'technical_level': 'moderate'
                })
            )

            db.session.add(prompt)
            db.session.commit()

            return {'message': 'Prompt created successfully', 'prompt': prompt.to_dict()}, 201

        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def update_prompt(store_id: int, user_id: int, prompt_id: int, prompt_data: dict) -> tuple:
        """
        Update an existing prompt.

        Parameters:
            store_id: ID of the store
            user_id: ID of the store owner
            prompt_id: ID of the prompt to update
            prompt_data: Updated prompt details

        Returns:
            tuple: (response_dict, status_code)
                response_dict: Contains success message and updated prompt
                status_code: 200 for success, 404/400 for errors

        Raises:
            Exception: If update fails or template syntax is invalid
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            prompt = Prompt.query.filter_by(id=prompt_id, store_id=store_id).first()
            if not prompt:
                return {'error': 'Prompt not found'}, 404

            # Validate template syntax if provided
            if 'template' in prompt_data:
                try:
                    jinja2.Template(prompt_data['template'])
                except Exception as e:
                    return {'error': f'Invalid template syntax: {str(e)}'}, 400

            # Update fields
            updateable_fields = [
                'name', 'description', 'template', 'is_default', 'is_active',
                'variables', 'tone', 'target_audience', 'writing_style',
                'seo_keywords_focus', 'description_length', 'key_features',
                'brand_voice', 'industry_specific', 'custom_instructions',
                'example_description', 'avoid_words', 'must_include_elements',
                'template_sections'
            ]

            for field in updateable_fields:
                if field in prompt_data:
                    setattr(prompt, field, prompt_data[field])

            prompt.updated_at = datetime.utcnow()
            db.session.commit()

            return {'message': 'Prompt updated successfully', 'prompt': prompt.to_dict()}, 200

        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def delete_prompt(store_id: int, user_id: int, prompt_id: int) -> tuple:
        """
        Delete a prompt.

        Parameters:
            store_id: ID of the store
            user_id: ID of the store owner
            prompt_id: ID of the prompt to delete

        Returns:
            tuple: (response_dict, status_code)
                response_dict: Contains success message or error
                status_code: 200 for success, 404/400 for errors

        Raises:
            Exception: If deletion fails
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            prompt = Prompt.query.filter_by(id=prompt_id, store_id=store_id).first()
            if not prompt:
                return {'error': 'Prompt not found'}, 404

            if prompt.is_default:
                return {'error': 'Cannot delete default prompt'}, 400

            db.session.delete(prompt)
            db.session.commit()

            return {'message': 'Prompt deleted successfully'}, 200

        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def render_prompt(prompt: Prompt, context: Dict[str, Any]) -> str:
        """
        Render a prompt template with given context.

        Parameters:
            prompt: Prompt object containing the template
            context: Variables to render in the template

        Returns:
            Rendered prompt text

        Raises:
            Exception: If template rendering fails
        """
        try:
            template = jinja2.Template(prompt.template)
            return template.render(**context)
        except Exception as e:
            raise Exception(f"Failed to render prompt template: {str(e)}")

    @staticmethod
    def render_prompt_preview(template_str: str, context: Dict[str, Any]) -> str:
        """
        Preview a prompt template with sample data.

        Parameters:
            template_str: Template string to render
            context: Variables to render in the template

        Returns:
            Rendered preview text

        Raises:
            Exception: If preview rendering fails
        """
        try:
            # Add default values for missing context
            default_context: Dict[str, Any] = {
                'product_title': 'Sample Product',
                'original_description': 'This is a sample product description.',
                'tone': 'professional',
                'target_audience': 'general',
                'writing_style': 'descriptive',
                'seo_keywords_focus': 'balanced',
                'description_length': 'medium',
                'key_features': ['Feature 1', 'Feature 2'],
                'brand_voice': {
                    'personality': 'professional',
                    'emotion': 'neutral',
                    'formality': 'formal'
                },
                'industry_specific': {
                    'industry': 'General',
                    'technical_level': 'moderate'
                }
            }

            # Merge provided context with defaults
            merged_context = {**default_context, **context}

            # Render template
            template = jinja2.Template(template_str)
            return template.render(**merged_context)
        except Exception as e:
            raise Exception(f"Failed to preview prompt template: {str(e)}")

    @staticmethod
    def get_available_options() -> Tuple[Dict[str, Union[List[str], Dict[str, List[str]]]], int]:
        """
        Get available options for prompt preferences.

        Returns:
            tuple: (options_dict, status_code)
                options_dict: Contains all available options for prompts
                status_code: 200 for success
        """
        return {
            'tones': [
                'professional', 'casual', 'friendly', 'formal', 'technical',
                'conversational', 'enthusiastic', 'authoritative'
            ],
            'target_audiences': [
                'general', 'technical', 'business', 'casual', 'luxury',
                'budget-conscious', 'professionals', 'enthusiasts'
            ],
            'writing_styles': [
                'descriptive', 'technical', 'persuasive', 'informative',
                'narrative', 'comparative', 'minimalist'
            ],
            'seo_keywords_focus': [
                'balanced', 'aggressive', 'minimal', 'natural'
            ],
            'description_lengths': [
                'short', 'medium', 'long', 'comprehensive'
            ],
            'brand_voice_options': {
                'personality': [
                    'professional', 'friendly', 'expert', 'innovative',
                    'traditional', 'luxurious', 'playful'
                ],
                'emotion': [
                    'neutral', 'positive', 'excited', 'confident',
                    'empathetic', 'passionate'
                ],
                'formality': [
                    'formal', 'semi-formal', 'casual', 'conversational'
                ]
            },
            'technical_levels': [
                'basic', 'moderate', 'advanced', 'expert'
            ],
            'template_sections': [
                'introduction', 'key_features', 'benefits', 'specifications',
                'use_cases', 'testimonials', 'call_to_action', 'warranty_info',
                'shipping_info', 'care_instructions'
            ]
        }, 200 