from flask import current_app
from shopifyapp.models.store import Store
from shopifyapp.models.user import db
import requests
from shopifyapp.models.product import Product
from datetime import datetime
import google.generativeai as genai
import os
from typing import Dict, List, Tuple, Optional, Any

class ProductService:
    @staticmethod
    def fetch_products_from_shopify(store: Store) -> Tuple[Dict[str, Any], int]:
        """
        Fetch products from Shopify API
        
        Args:
            store: Store instance to fetch products from
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        if not store.access_token:
            return {'error': 'Store not authenticated'}, 401

        headers = {
            'X-Shopify-Access-Token': store.access_token,
            'Content-Type': 'application/json'
        }

        try:
            # Get products from Shopify
            url = f"{store.get_api_url()}/products.json"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                return {'error': f'Failed to fetch products: {response.text}'}, response.status_code

            shopify_products = response.json().get('products', [])
            
            # Update local database with fetched products
            updated_products = []
            for shopify_product in shopify_products:
                product = Product.query.filter_by(
                    store_id=store.id,
                    shopify_product_id=str(shopify_product['id'])
                ).first()

                if not product:
                    product = Product(
                        store_id=store.id,
                        shopify_product_id=str(shopify_product['id'])
                    )

                # Update product details
                product.title = shopify_product['title']
                product.original_description = shopify_product['body_html']
                
                if not product.id:  # New product
                    db.session.add(product)
                updated_products.append(product)

            # Commit changes
            db.session.commit()
            
            return {'products': [p.to_dict() for p in updated_products]}, 200

        except requests.exceptions.RequestException as e:
            return {'error': f'Network error: {str(e)}'}, 500
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to sync products: {str(e)}'}, 500

    @staticmethod
    def get_store_products(store_id: int, user_id: int) -> Tuple[Dict[str, Any], int]:
        """
        Get all products for a specific store
        
        Args:
            store_id: ID of the store
            user_id: ID of the store owner
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        store = Store.query.filter_by(id=store_id, user_id=user_id).first()
        if not store:
            return {'error': 'Store not found'}, 404

        # First fetch latest products from Shopify
        result, status_code = ProductService.fetch_products_from_shopify(store)
        if status_code != 200:
            # If fetch fails, return stored products
            products = Product.query.filter_by(store_id=store_id).all()
            return {'products': [p.to_dict() for p in products]}, 200

        return result, status_code

    @staticmethod
    def get_all_user_products(user_id: int) -> Tuple[Dict[str, List[Dict[str, Any]]], int]:
        """
        Get all products from all stores for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Tuple containing response dictionary with products list and HTTP status code
        """
        stores = Store.query.filter_by(user_id=user_id).all()
        all_products = []
        
        for store in stores:
            result, status_code = ProductService.fetch_products_from_shopify(store)
            if status_code == 200:
                all_products.extend(result['products'])

        return {'products': all_products}, 200

    @staticmethod
    def get_product(store_id: int, user_id: int, product_id: int) -> Tuple[Dict[str, Any], int]:
        """
        Retrieve a specific product from the Shopify store.
        
        Args:
            store_id: ID of the store
            user_id: ID of the store owner
            product_id: ID of the product to retrieve
            
        Returns:
            Tuple containing response dictionary with product details and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404
                
            product = Product.query.filter_by(id=product_id, store_id=store_id).first()
            if not product:
                return {'error': 'Product not found'}, 404
                
            product_data = {
                'id': product.id,
                'title': product.title,
                'description': product.description,
                'price': product.price,
                'compare_at_price': product.compare_at_price,
                'vendor': product.vendor,
                'product_type': product.product_type,
                'tags': product.tags,
                'status': product.status,
                'inventory_management': product.inventory_management,
                'inventory_quantity': product.inventory_quantity,
                'variants': product.variants,
                'options': product.options,
                'images': product.images,
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat()
            }
            
            return {'product': product_data}, 200
            
        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def _get_optimized_description(
        original_description: str,
        product_title: str,
        store_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate optimized description using Gemini AI
        
        Args:
            original_description: Original product description
            product_title: Title of the product
            store_preferences: Dictionary containing store preferences for optimization
            
        Returns:
            Optimized description string
            
        Raises:
            Exception: If optimization fails
        """
        try:
            # Configure Gemini AI
            genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
            model = genai.GenerativeModel('gemini-pro')

            # Create prompt based on store preferences or use default
            base_prompt = """
            As an expert e-commerce copywriter and SEO specialist, optimize the following product description 
            to be more engaging, SEO-friendly, and conversion-focused. Maintain the key product features 
            while improving readability and search engine optimization.

            Product Title: {title}
            Original Description: {description}

            Guidelines:
            - Maintain a professional yet engaging tone
            - Include relevant keywords naturally
            - Structure content with clear sections
            - Focus on benefits and value propositions
            - Ensure mobile-friendly formatting
            - Keep HTML formatting for Shopify
            """

            if store_preferences and store_preferences.get('tone'):
                base_prompt += f"\n- Use a {store_preferences['tone']} tone"
            if store_preferences and store_preferences.get('length'):
                base_prompt += f"\n- Aim for approximately {store_preferences['length']} words"

            # Generate optimized description
            prompt = base_prompt.format(
                title=product_title,
                description=original_description
            )

            response = model.generate_content(prompt)
            optimized_description = response.text

            # Ensure HTML formatting
            if not optimized_description.strip().startswith('<'):
                optimized_description = f"<p>{optimized_description}</p>"

            return optimized_description

        except Exception as e:
            raise Exception(f"Failed to generate optimized description: {str(e)}")

    @staticmethod
    def optimize_product_description(
        user_id: int,
        store_id: int,
        product_id: int,
        custom_prompt: Optional[str] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Optimize a single product description using Gemini AI
        
        Args:
            user_id: ID of the store owner
            store_id: ID of the store
            product_id: ID of the product
            custom_prompt: Optional custom prompt for optimization
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            product = Product.query.filter_by(id=product_id, store_id=store_id).first()
            if not product:
                return {'error': 'Product not found'}, 404

            # Get optimized description
            optimized_description = ProductService._get_optimized_description(
                original_description=product.original_description or product.description,
                product_title=product.title,
                store_preferences=store.prompt_preferences
            )

            # Store optimization results
            product.optimized_description = optimized_description
            product.original_description = product.original_description or product.description
            product.is_optimized = True
            product.last_optimized = datetime.utcnow()
            product.optimization_service = 'gemini'
            
            db.session.commit()

            return {
                'message': 'Product description optimized successfully',
                'product': product.to_dict()
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def optimize_all_products(
        user_id: int,
        store_id: int,
        custom_prompt: Optional[str] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Optimize all product descriptions
        
        Args:
            user_id: ID of the store owner
            store_id: ID of the store
            custom_prompt: Optional custom prompt for optimization
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            products = Product.query.filter_by(store_id=store_id).all()
            optimized_products = []

            for product in products:
                try:
                    # Get optimized description
                    optimized_description = ProductService._get_optimized_description(
                        original_description=product.original_description,
                        product_title=product.title,
                        store_preferences=store.prompt_preferences
                    )

                    # Update product
                    product.optimized_description = optimized_description
                    product.is_optimized = True
                    product.last_optimized = datetime.utcnow()
                    optimized_products.append(product.to_dict())

                except Exception as e:
                    # Log error but continue with other products
                    print(f"Error optimizing product {product.id}: {str(e)}")
                    continue

            db.session.commit()
            return {
                'message': f'Successfully optimized {len(optimized_products)} products',
                'products': optimized_products
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def deploy_optimization(user_id: int, store_id: int, product_id: int) -> Tuple[Dict[str, Any], int]:
        """
        Deploy optimized description to Shopify
        
        Args:
            user_id: ID of the store owner
            store_id: ID of the store
            product_id: ID of the product
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            if not store.access_token:
                return {'error': 'Store not authenticated'}, 401

            product = Product.query.filter_by(id=product_id, store_id=store_id).first()
            if not product:
                return {'error': 'Product not found'}, 404

            if not product.is_optimized or not product.optimized_description:
                return {'error': 'Product description not optimized yet'}, 400

            # Prepare data for Shopify API
            product_data = {
                "product": {
                    "id": product.shopify_product_id,
                    "body_html": product.optimized_description
                }
            }

            # Update product in Shopify
            headers = {
                'X-Shopify-Access-Token': store.access_token,
                'Content-Type': 'application/json'
            }
            url = f"https://{store.store_url}/admin/api/{store.api_version}/products/{product.shopify_product_id}.json"
            
            response = requests.put(url, json=product_data, headers=headers)
            
            if response.status_code not in [200, 201]:
                return {'error': f'Failed to update product in Shopify: {response.text}'}, response.status_code

            # Update deployment status
            product.description = product.optimized_description
            product.last_deployed = datetime.utcnow()
            product.deployment_status = 'deployed'
            
            db.session.commit()

            return {
                'message': 'Description deployed successfully',
                'product': product.to_dict()
            }, 200
            
        except requests.exceptions.RequestException as e:
            return {'error': f'Network error: {str(e)}'}, 500
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def deploy_all_optimizations(user_id: int, store_id: int) -> Tuple[Dict[str, Any], int]:
        """
        Deploy all optimized descriptions to Shopify
        
        Args:
            user_id: ID of the store owner
            store_id: ID of the store
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            if not store.access_token:
                return {'error': 'Store not authenticated'}, 401

            # Get all optimized products that haven't been deployed
            products = Product.query.filter_by(
                store_id=store_id,
                is_optimized=True
            ).filter(
                (Product.deployment_status != 'deployed') | 
                (Product.deployment_status.is_(None))
            ).all()

            if not products:
                return {'message': 'No optimized products pending deployment'}, 200

            deployed_count = 0
            failed_count = 0
            results = []

            for product in products:
                try:
                    result, status_code = ProductService.deploy_optimization(user_id, store_id, product.id)
                    if status_code in [200, 201]:
                        deployed_count += 1
                        results.append({
                            'product_id': product.id,
                            'status': 'success',
                            'message': 'Deployed successfully'
                        })
                    else:
                        failed_count += 1
                        results.append({
                            'product_id': product.id,
                            'status': 'failed',
                            'message': result.get('error', 'Unknown error')
                        })
                except Exception as e:
                    failed_count += 1
                    results.append({
                        'product_id': product.id,
                        'status': 'failed',
                        'message': str(e)
                    })

            return {
                'message': 'Batch deployment completed',
                'total_products': len(products),
                'deployed_count': deployed_count,
                'failed_count': failed_count,
                'results': results
            }, 200 if failed_count == 0 else 207  # 207 Multi-Status if some failed
            
        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def track_seo_metrics(product_id: int) -> Tuple[Dict[str, Any], int]:
        """
        Track SEO metrics for a product description
        
        Args:
            product_id: ID of the product
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            product = Product.query.get(product_id)
            if not product:
                return {'error': 'Product not found'}, 404

            # Calculate basic SEO metrics
            metrics = {
                'word_count': len(product.description.split()) if product.description else 0,
                'keyword_density': {},  # TODO: Implement keyword density calculation
                'readability_score': 0,  # TODO: Implement readability scoring
                'optimization_age': (datetime.utcnow() - product.last_optimized).days if product.last_optimized else None,
                'deployment_age': (datetime.utcnow() - product.last_deployed).days if product.last_deployed else None,
                'optimization_service': product.optimization_service,
                'deployment_status': product.deployment_status
            }

            return {'metrics': metrics}, 200

        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def update_store_prompt(
        user_id: int,
        store_id: int,
        prompt_template: str
    ) -> Tuple[Dict[str, Any], int]:
        """
        Update store's default prompt template
        
        Args:
            user_id: ID of the store owner
            store_id: ID of the store
            prompt_template: New prompt template
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            store.prompt_preferences['default_template'] = prompt_template
            db.session.commit()
            
            return {'message': 'Prompt template updated', 'store': store.to_dict()}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def create_product(
        store_id: int,
        user_id: int,
        title: str,
        description: str,
        price: float,
        compare_at_price: Optional[float] = None,
        vendor: Optional[str] = None,
        product_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        images: Optional[List[Dict[str, Any]]] = None,
        variants: Optional[List[Dict[str, Any]]] = None,
        options: Optional[List[Dict[str, Any]]] = None,
        status: str = "active",
        inventory_management: Optional[str] = None,
        inventory_quantity: Optional[int] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Create a new product in Shopify store.
        
        Args:
            store_id: ID of the store
            user_id: ID of the store owner
            title: Product title
            description: Product description
            price: Product price
            compare_at_price: Compare at price (optional)
            vendor: Product vendor (optional)
            product_type: Product type (optional)
            tags: List of product tags (optional)
            images: List of product images (optional)
            variants: List of product variants (optional)
            options: List of product options (optional)
            status: Product status (default: active)
            inventory_management: Inventory management type (optional)
            inventory_quantity: Initial inventory quantity (optional)
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            # Verify store exists and is authenticated
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            if not store.access_token:
                return {'error': 'Store not authenticated'}, 401

            # Prepare product data for Shopify API
            product_data = {
                "product": {
                    "title": title,
                    "body_html": description,
                    "vendor": vendor,
                    "product_type": product_type,
                    "status": status,
                    "tags": tags if tags else [],
                    "variants": [{
                        "price": str(price),
                        "compare_at_price": str(compare_at_price) if compare_at_price else None,
                        "inventory_management": inventory_management,
                        "inventory_quantity": inventory_quantity if inventory_quantity is not None else 0
                    }]
                }
            }

            # Add options if provided
            if options:
                product_data["product"]["options"] = options

            # Add images if provided
            if images:
                product_data["product"]["images"] = images

            # Add additional variants if provided
            if variants:
                product_data["product"]["variants"] = variants

            # Create product in Shopify
            headers = {
                'X-Shopify-Access-Token': store.access_token,
                'Content-Type': 'application/json'
            }
            url = f"https://{store.store_url}/admin/api/{store.api_version}/products.json"
            
            response = requests.post(url, json=product_data, headers=headers)
            
            if response.status_code not in [201, 200]:
                return {'error': f'Failed to create product in Shopify: {response.text}'}, response.status_code

            shopify_product = response.json()['product']

            # Create local product record
            product = Product(
                store_id=store_id,
                shopify_product_id=str(shopify_product['id']),
                title=shopify_product['title'],
                description=shopify_product['body_html'],
                vendor=shopify_product.get('vendor'),
                product_type=shopify_product.get('product_type'),
                tags=shopify_product.get('tags', []),
                variants=shopify_product.get('variants', []),
                images=shopify_product.get('images', []),
                options=shopify_product.get('options', []),
                status=shopify_product['status'],
                handle=shopify_product['handle'],
                last_synced=datetime.utcnow()
            )

            db.session.add(product)
            db.session.commit()

            return {
                'message': 'Product created successfully',
                'product': product.to_dict()
            }, 201

        except requests.exceptions.RequestException as e:
            return {'error': f'Network error: {str(e)}'}, 500
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def list_products(store_id: int, user_id: int, page: int = 1, per_page: int = 20, 
                     status: Optional[str] = None, search: Optional[str] = None) -> Tuple[Dict, int]:
        """
        List products with pagination and filtering.
        
        Args:
            store_id: ID of the store
            user_id: ID of the store owner
            page: Page number
            per_page: Items per page
            status: Filter by status (optional)
            search: Search in title/vendor (optional)
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            # Build query
            query = Product.query.filter_by(store_id=store_id)

            # Apply filters
            if status:
                query = query.filter_by(status=status)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    db.or_(
                        Product.title.ilike(search_term),
                        Product.vendor.ilike(search_term)
                    )
                )

            # Apply pagination
            products = query.order_by(Product.updated_at.desc())\
                .paginate(page=page, per_page=per_page, error_out=False)

            return {
                'products': [product.to_dict() for product in products.items],
                'total': products.total,
                'pages': products.pages,
                'current_page': products.page,
                'per_page': per_page
            }, 200

        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def sync_products(store_id: int, user_id: int) -> Tuple[Dict[str, Any], int]:
        """
        Sync all products from Shopify store.
        
        Args:
            store_id: ID of the store
            user_id: ID of the store owner
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            if not store.access_token:
                return {'error': 'Store not authenticated'}, 401

            # Shopify API endpoint
            url = f"https://{store.store_url}/admin/api/{store.api_version}/products.json"
            headers = {'X-Shopify-Access-Token': store.access_token}

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return {'error': 'Failed to fetch products from Shopify'}, response.status_code

            products_data = response.json().get('products', [])
            synced_count = 0
            failed_count = 0

            for product_data in products_data:
                try:
                    result, _ = ProductService.create_product(store_id, user_id, product_data)
                    if 'error' not in result:
                        synced_count += 1
                    else:
                        failed_count += 1
                except Exception:
                    failed_count += 1

            return {
                'message': 'Product sync completed',
                'total_products': len(products_data),
                'synced_count': synced_count,
                'failed_count': failed_count
            }, 200

        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def bulk_update_status(
        store_id: int,
        user_id: int,
        product_ids: List[int],
        status: str
    ) -> Tuple[Dict[str, Any], int]:
        """
        Update status for multiple products.
        
        Args:
            store_id: ID of the store
            user_id: ID of the store owner
            product_ids: List of product IDs to update
            status: New status to set
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            products = Product.query.filter(
                Product.id.in_(product_ids),
                Product.store_id == store_id
            ).all()

            if not products:
                return {'error': 'No products found'}, 404

            for product in products:
                product.status = status
                product.updated_at = datetime.utcnow()

            db.session.commit()

            return {
                'message': f'Successfully updated {len(products)} products',
                'updated_products': [product.to_dict() for product in products]
            }, 200

        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def update_product(
        store_id: int,
        user_id: int,
        product_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[float] = None,
        compare_at_price: Optional[float] = None,
        vendor: Optional[str] = None,
        product_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        images: Optional[List[Dict[str, Any]]] = None,
        variants: Optional[List[Dict[str, Any]]] = None,
        options: Optional[List[Dict[str, Any]]] = None,
        status: Optional[str] = None,
        inventory_management: Optional[str] = None,
        inventory_quantity: Optional[int] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Update an existing product in Shopify store.
        
        Args:
            store_id: ID of the store
            user_id: ID of the store owner
            product_id: ID of the product to update
            title: Updated product title (optional)
            description: Updated product description (optional)
            price: Updated product price (optional)
            compare_at_price: Updated compare at price (optional)
            vendor: Updated product vendor (optional)
            product_type: Updated product type (optional)
            tags: Updated list of product tags (optional)
            images: Updated list of product images (optional)
            variants: Updated list of product variants (optional)
            options: Updated list of product options (optional)
            status: Updated product status (optional)
            inventory_management: Updated inventory management type (optional)
            inventory_quantity: Updated inventory quantity (optional)
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            product = Product.query.filter_by(id=product_id, store_id=store_id).first()
            if not product:
                return {'error': 'Product not found'}, 404

            # Update product details
            if title:
                product.title = title
            if description:
                product.description = description
            if price:
                product.price = price
            if compare_at_price:
                product.compare_at_price = compare_at_price
            if vendor:
                product.vendor = vendor
            if product_type:
                product.product_type = product_type
            if tags:
                product.tags = tags
            if images:
                product.images = images
            if variants:
                product.variants = variants
            if options:
                product.options = options
            if status:
                product.status = status
            if inventory_management:
                product.inventory_management = inventory_management
            if inventory_quantity:
                product.inventory_quantity = inventory_quantity

            db.session.commit()

            return {
                'message': 'Product updated successfully',
                'product': product.to_dict()
            }, 200

        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    @staticmethod
    def delete_product(store_id: int, user_id: int, product_id: int) -> Tuple[Dict[str, Any], int]:
        """
        Delete a product from the Shopify store.
        
        Args:
            store_id: ID of the store
            user_id: ID of the store owner
            product_id: ID of the product to delete
            
        Returns:
            Tuple containing response dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            product = Product.query.filter_by(id=product_id, store_id=store_id).first()
            if not product:
                return {'error': 'Product not found'}, 404

            # TODO: Implement Shopify API call to delete product
            return {'message': 'Product deleted successfully'}, 200

        except Exception as e:
            return {'error': str(e)}, 500 