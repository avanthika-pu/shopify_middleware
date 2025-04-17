import unittest
from unittest.mock import patch, MagicMock
from shopifyapp.services.seo_service import SEOService
from shopifyapp.models.store import Store
from shopifyapp.models.product import Product
from shopifyapp.models.user import db
import os

# Mock Prompt model for testing
class Prompt(db.Model):
    __tablename__ = 'prompts'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    store = db.relationship('Store', back_populates='prompts')

class TestSEOService(unittest.TestCase):
    def setUp(self):
        # Mock environment variable
        os.environ['GEMINI_API_KEY'] = 'test_api_key'
        
        # Mock database session
        self.db_session = MagicMock()
        db.session = self.db_session
        
        # Test data
        self.user_id = 1
        self.store_id = 1
        self.product_id = 1
        self.test_title = "Test Product"
        self.test_description = "Original product description"
        self.test_preferences = {
            'tone': 'professional',
            'length': '200',
            'keywords': ['test', 'product']
        }
        
        # Mock store and product
        self.store = Store(id=self.store_id, user_id=self.user_id, prompt_preferences=self.test_preferences)
        self.product = Product(
            id=self.product_id,
            store_id=self.store_id,
            title=self.test_title,
            original_description=self.test_description
        )

    @patch('google.generativeai.GenerativeModel')
    def test_optimize_single_product(self, mock_genai_model):
        # Mock Gemini AI response
        mock_response = MagicMock()
        mock_response.text = "<p>Optimized product description</p>"
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_genai_model.return_value = mock_model_instance

        # Mock database queries
        with patch('shopifyapp.models.store.Store.query') as mock_store_query:
            with patch('shopifyapp.models.product.Product.query') as mock_product_query:
                mock_store_query.filter_by.return_value.first.return_value = self.store
                mock_product_query.filter_by.return_value.first.return_value = self.product

                # Test optimization
                result, status_code = SEOService.optimize_product_description(
                    user_id=self.user_id,
                    store_id=self.store_id,
                    product_id=self.product_id
                )

                # Assertions
                self.assertEqual(status_code, 200)
                self.assertEqual(result['message'], 'Product description optimized successfully')
                self.assertTrue(self.product.is_optimized)
                self.assertIsNotNone(self.product.last_optimized)
                self.assertEqual(self.product.optimized_description, "<p>Optimized product description</p>")

                # Verify Gemini AI was called with correct prompt
                mock_model_instance.generate_content.assert_called_once()
                prompt_arg = mock_model_instance.generate_content.call_args[0][0]
                self.assertIn(self.test_title, prompt_arg)
                self.assertIn(self.test_description, prompt_arg)
                self.assertIn(self.test_preferences['tone'], prompt_arg)

    @patch('google.generativeai.GenerativeModel')
    def test_optimize_all_products(self, mock_genai_model):
        # Mock Gemini AI response
        mock_response = MagicMock()
        mock_response.text = "<p>Optimized product description</p>"
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_genai_model.return_value = mock_model_instance

        # Create multiple test products
        test_products = [
            Product(id=1, store_id=self.store_id, title="Product 1", original_description="Description 1"),
            Product(id=2, store_id=self.store_id, title="Product 2", original_description="Description 2")
        ]

        # Mock database queries
        with patch('shopifyapp.models.store.Store.query') as mock_store_query:
            with patch('shopifyapp.models.product.Product.query') as mock_product_query:
                mock_store_query.filter_by.return_value.first.return_value = self.store
                mock_product_query.filter_by.return_value.all.return_value = test_products

                # Test optimization
                result, status_code = SEOService.optimize_all_products(
                    user_id=self.user_id,
                    store_id=self.store_id
                )

                # Assertions
                self.assertEqual(status_code, 200)
                self.assertIn('Successfully optimized 2 products', result['message'])
                self.assertEqual(len(result['products']), 2)
                
                # Verify Gemini AI was called for each product
                self.assertEqual(mock_model_instance.generate_content.call_count, 2)

    def test_error_handling(self):
        # Test store not found
        with patch('shopifyapp.models.store.Store.query') as mock_store_query:
            mock_store_query.filter_by.return_value.first.return_value = None
            
            result, status_code = SEOService.optimize_product_description(
                user_id=self.user_id,
                store_id=self.store_id,
                product_id=self.product_id
            )
            
            self.assertEqual(status_code, 404)
            self.assertEqual(result['error'], 'Store not found')

if __name__ == '__main__':
    unittest.main() 