import unittest
from unittest.mock import patch, MagicMock
from shopifyapp.services.prompt_service import PromptService
from shopifyapp.models.store import Store
from shopifyapp.models.prompt import Prompt
from shopifyapp.models.user import db

class TestPromptService(unittest.TestCase):
    def setUp(self):
        # Mock database session
        self.db_session = MagicMock()
        db.session = self.db_session
        
        # Test data
        self.user_id = 1
        self.store_id = 1
        self.prompt_id = 1
        self.test_preferences = {
            'tone': 'professional',
            'target_audience': 'general',
            'writing_style': 'descriptive'
        }
        
        # Mock store
        self.store = Store(id=self.store_id, user_id=self.user_id, prompt_preferences=self.test_preferences)
        
        # Mock prompt
        self.prompt = Prompt(
            id=self.prompt_id,
            store_id=self.store_id,
            name="Test Prompt",
            description="Test Description",
            template="Test template with {{product_title}}",
            variables={'product_title': {'type': 'string', 'required': True}}
        )

    def test_get_prompts(self):
        # Mock database queries
        with patch('shopifyapp.models.store.Store.query') as mock_store_query:
            with patch('shopifyapp.models.prompt.Prompt.query') as mock_prompt_query:
                mock_store_query.filter_by.return_value.first.return_value = self.store
                mock_prompt_query.filter_by.return_value.all.return_value = [self.prompt]

                # Test get prompts
                result, status_code = PromptService.get_prompts(
                    store_id=self.store_id,
                    user_id=self.user_id
                )

                # Assertions
                self.assertEqual(status_code, 200)
                self.assertEqual(len(result['prompts']), 1)
                self.assertEqual(result['prompts'][0]['name'], "Test Prompt")

    def test_create_prompt(self):
        # Test data
        prompt_data = {
            'name': 'New Prompt',
            'description': 'New Description',
            'template': 'New template with {{product_title}}',
            'variables': {'product_title': {'type': 'string', 'required': True}}
        }

        # Mock database queries
        with patch('shopifyapp.models.store.Store.query') as mock_store_query:
            mock_store_query.filter_by.return_value.first.return_value = self.store

            # Test create prompt
            result, status_code = PromptService.create_prompt(
                store_id=self.store_id,
                user_id=self.user_id,
                prompt_data=prompt_data
            )

            # Assertions
            self.assertEqual(status_code, 201)
            self.assertEqual(result['message'], 'Prompt created successfully')
            self.assertEqual(result['prompt']['name'], 'New Prompt')

            # Verify database operations
            self.db_session.add.assert_called_once()
            self.db_session.commit.assert_called_once()

    def test_update_prompt(self):
        # Test data
        prompt_data = {
            'name': 'Updated Prompt',
            'description': 'Updated Description'
        }

        # Mock database queries
        with patch('shopifyapp.models.store.Store.query') as mock_store_query:
            with patch('shopifyapp.models.prompt.Prompt.query') as mock_prompt_query:
                mock_store_query.filter_by.return_value.first.return_value = self.store
                mock_prompt_query.filter_by.return_value.first.return_value = self.prompt

                # Test update prompt
                result, status_code = PromptService.update_prompt(
                    store_id=self.store_id,
                    user_id=self.user_id,
                    prompt_id=self.prompt_id,
                    prompt_data=prompt_data
                )

                # Assertions
                self.assertEqual(status_code, 200)
                self.assertEqual(result['message'], 'Prompt updated successfully')
                self.assertEqual(result['prompt']['name'], 'Updated Prompt')
                self.assertEqual(self.prompt.name, 'Updated Prompt')

                # Verify database operations
                self.db_session.commit.assert_called_once()

    def test_delete_prompt(self):
        # Mock database queries
        with patch('shopifyapp.models.store.Store.query') as mock_store_query:
            with patch('shopifyapp.models.prompt.Prompt.query') as mock_prompt_query:
                mock_store_query.filter_by.return_value.first.return_value = self.store
                mock_prompt_query.filter_by.return_value.first.return_value = self.prompt

                # Test delete prompt
                result, status_code = PromptService.delete_prompt(
                    store_id=self.store_id,
                    user_id=self.user_id,
                    prompt_id=self.prompt_id
                )

                # Assertions
                self.assertEqual(status_code, 200)
                self.assertEqual(result['message'], 'Prompt deleted successfully')

                # Verify database operations
                self.db_session.delete.assert_called_once_with(self.prompt)
                self.db_session.commit.assert_called_once()

    def test_render_prompt(self):
        # Test data
        context = {
            'product_title': 'Test Product',
            'original_description': 'Test Description',
            'tone': 'professional'
        }

        # Test render prompt
        rendered_text = PromptService.render_prompt(self.prompt, context)

        # Assertions
        self.assertIn('Test Product', rendered_text)
        self.assertEqual(rendered_text, 'Test template with Test Product')

    def test_error_handling(self):
        # Test store not found
        with patch('shopifyapp.models.store.Store.query') as mock_store_query:
            mock_store_query.filter_by.return_value.first.return_value = None
            
            result, status_code = PromptService.get_prompts(
                store_id=self.store_id,
                user_id=self.user_id
            )
            
            self.assertEqual(status_code, 404)
            self.assertEqual(result['error'], 'Store not found')

if __name__ == '__main__':
    unittest.main() 