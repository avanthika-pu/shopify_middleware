from datetime import datetime
from shopifyapp.models.user import db

class Prompt(db.Model):
    __tablename__ = 'prompts'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    template_name = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, success, failed
    response_time = db.Column(db.Float)  # in seconds
    error_message = db.Column(db.Text)
    metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Prompt configuration
    tone = db.Column(db.String(50), default='professional')
    target_audience = db.Column(db.String(50), default='general')
    writing_style = db.Column(db.String(50), default='descriptive')
    seo_keywords_focus = db.Column(db.String(20), default='balanced')
    description_length = db.Column(db.String(20), default='medium')
    
    # JSON fields for complex data
    key_features = db.Column(db.JSON, default=list)
    brand_voice = db.Column(db.JSON, default={
        'personality': 'professional',
        'emotion': 'neutral',
        'formality': 'formal'
    })
    industry_specific = db.Column(db.JSON, default={
        'industry': None,
        'specializations': [],
        'technical_level': 'moderate'
    })
    
    # Additional configuration
    custom_instructions = db.Column(db.Text)
    example_description = db.Column(db.Text)
    avoid_words = db.Column(db.JSON, default=list)
    must_include_elements = db.Column(db.JSON, default=list)
    template_sections = db.Column(db.JSON, default=[
        'introduction',
        'key_features',
        'benefits',
        'specifications',
        'call_to_action'
    ])

    # Relationships
    store = db.relationship('Store', back_populates='prompts')

    def to_dict(self):
        """Convert prompt to dictionary"""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'template_name': self.template_name,
            'content': self.content,
            'response': self.response,
            'status': self.status,
            'response_time': self.response_time,
            'error_message': self.error_message,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def create_default_prompt(store_id):
        """Create a default prompt template for a store"""
        return Prompt(
            store_id=store_id,
            template_name="Default SEO Optimization",
            content="Default template for SEO-optimized product descriptions",
            response="""
            As an expert e-commerce copywriter and SEO specialist, optimize the following product description 
            to be more engaging, SEO-friendly, and conversion-focused. Maintain the key product features 
            while improving readability and search engine optimization.

            Product Title: {{product_title}}
            Original Description: {{original_description}}

            Guidelines:
            - Maintain a {{tone}} tone
            - Target {{target_audience}} audience
            - Use {{writing_style}} writing style
            - Focus on {{seo_keywords_focus}} SEO optimization
            - Aim for {{description_length}} length
            {% if key_features %}
            - Highlight these key features: {{key_features|join(', ')}}
            {% endif %}
            {% if brand_voice %}
            - Brand Voice:
              * Personality: {{brand_voice.personality}}
              * Emotion: {{brand_voice.emotion}}
              * Formality: {{brand_voice.formality}}
            {% endif %}
            {% if industry_specific %}
            - Industry Specifics:
              * Industry: {{industry_specific.industry}}
              * Technical Level: {{industry_specific.technical_level}}
            {% endif %}
            {% if custom_instructions %}
            - Custom Instructions: {{custom_instructions}}
            {% endif %}
            {% if avoid_words %}
            - Avoid these words: {{avoid_words|join(', ')}}
            {% endif %}
            {% if must_include_elements %}
            - Must include: {{must_include_elements|join(', ')}}
            {% endif %}
            """,
            status='success',
            response_time=0.0,
            metadata={
                'product_title': {'type': 'string', 'required': True},
                'original_description': {'type': 'string', 'required': True},
                'tone': {'type': 'string', 'required': True},
                'target_audience': {'type': 'string', 'required': True},
                'writing_style': {'type': 'string', 'required': True},
                'seo_keywords_focus': {'type': 'string', 'required': True},
                'description_length': {'type': 'string', 'required': True},
                'key_features': {'type': 'array', 'required': False},
                'brand_voice': {'type': 'object', 'required': False},
                'industry_specific': {'type': 'object', 'required': False},
                'custom_instructions': {'type': 'string', 'required': False},
                'avoid_words': {'type': 'array', 'required': False},
                'must_include_elements': {'type': 'array', 'required': False}
            }
        ) 