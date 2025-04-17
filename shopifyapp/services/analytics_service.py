from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from sqlalchemy import func, desc
from shopifyapp.models.store import Store
from shopifyapp.models.product import Product
from shopifyapp.models.prompt import Prompt
from shopifyapp.models.user import db

class AnalyticsService:
    @staticmethod
    def collect_prompt_metrics(
        store_id: int,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Collect metrics about prompt usage and performance
        
        Args:
            store_id: ID of the store
            user_id: ID of the store owner
            start_date: Start date for metrics collection
            end_date: End date for metrics collection
            
        Returns:
            Tuple containing metrics dictionary and HTTP status code
        """
        try:
            store = Store.query.filter_by(id=store_id, user_id=user_id).first()
            if not store:
                return {'error': 'Store not found'}, 404

            # Set default date range if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Query base
            query = db.session.query(Prompt).filter(
                Prompt.store_id == store_id,
                Prompt.created_at.between(start_date, end_date)
            )

            # Collect metrics
            total_prompts = query.count()
            successful_prompts = query.filter(Prompt.status == 'success').count()
            failed_prompts = query.filter(Prompt.status == 'failed').count()
            
            # Get average response time
            avg_response_time = db.session.query(
                func.avg(Prompt.response_time)
            ).filter(
                Prompt.store_id == store_id,
                Prompt.created_at.between(start_date, end_date),
                Prompt.response_time.isnot(None)
            ).scalar()

            # Get most used templates
            template_usage = db.session.query(
                Prompt.template_name,
                func.count(Prompt.id).label('usage_count')
            ).filter(
                Prompt.store_id == store_id,
                Prompt.created_at.between(start_date, end_date)
            ).group_by(Prompt.template_name).order_by(desc('usage_count')).limit(5).all()

            # Calculate success rate trend
            success_trend = []
            current_date = start_date
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                day_total = query.filter(Prompt.created_at.between(current_date, next_date)).count()
                day_success = query.filter(
                    Prompt.created_at.between(current_date, next_date),
                    Prompt.status == 'success'
                ).count()
                
                success_rate = (day_success / day_total * 100) if day_total > 0 else 0
                success_trend.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'success_rate': success_rate
                })
                current_date = next_date

            metrics = {
                'total_prompts': total_prompts,
                'successful_prompts': successful_prompts,
                'failed_prompts': failed_prompts,
                'success_rate': (successful_prompts / total_prompts * 100) if total_prompts > 0 else 0,
                'avg_response_time': float(avg_response_time) if avg_response_time else 0,
                'template_usage': [
                    {'template': t[0], 'count': t[1]} for t in template_usage
                ],
                'success_trend': success_trend
            }

            return {'metrics': metrics}, 200

        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def get_dashboard_data(
        user_id: int,
        store_id: Optional[int] = None,
        timeframe: str = 'last_30_days'
    ) -> Tuple[Dict[str, Any], int]:
        """
        Get aggregated data for the analytics dashboard
        
        Args:
            user_id: ID of the user
            store_id: Optional store ID to filter data
            timeframe: Time period for data (last_24h, last_7_days, last_30_days, last_90_days)
            
        Returns:
            Tuple containing dashboard data and HTTP status code
        """
        try:
            # Calculate date range based on timeframe
            end_date = datetime.utcnow()
            if timeframe == 'last_24h':
                start_date = end_date - timedelta(days=1)
            elif timeframe == 'last_7_days':
                start_date = end_date - timedelta(days=7)
            elif timeframe == 'last_90_days':
                start_date = end_date - timedelta(days=90)
            else:  # default to last 30 days
                start_date = end_date - timedelta(days=30)

            # Base query for stores
            stores_query = Store.query.filter_by(user_id=user_id)
            if store_id:
                stores_query = stores_query.filter_by(id=store_id)
            
            stores = stores_query.all()
            if not stores:
                return {'error': 'No stores found'}, 404

            dashboard_data = {
                'summary': {
                    'total_stores': len(stores),
                    'total_products': 0,
                    'total_optimizations': 0,
                    'total_prompts': 0
                },
                'stores': []
            }

            for store in stores:
                # Get store metrics
                store_metrics = {
                    'store_id': store.id,
                    'store_url': store.store_url,
                    'products_count': Product.query.filter_by(store_id=store.id).count(),
                    'optimized_products': Product.query.filter_by(
                        store_id=store.id,
                        is_optimized=True
                    ).count(),
                    'prompts_count': Prompt.query.filter(
                        Prompt.store_id == store.id,
                        Prompt.created_at.between(start_date, end_date)
                    ).count()
                }

                # Get prompt success metrics
                successful_prompts = Prompt.query.filter(
                    Prompt.store_id == store.id,
                    Prompt.created_at.between(start_date, end_date),
                    Prompt.status == 'success'
                ).count()

                store_metrics['success_rate'] = (
                    (successful_prompts / store_metrics['prompts_count'] * 100)
                    if store_metrics['prompts_count'] > 0 else 0
                )

                # Update summary
                dashboard_data['summary']['total_products'] += store_metrics['products_count']
                dashboard_data['summary']['total_optimizations'] += store_metrics['optimized_products']
                dashboard_data['summary']['total_prompts'] += store_metrics['prompts_count']

                dashboard_data['stores'].append(store_metrics)

            # Add trend data
            dashboard_data['trends'] = {
                'optimization_trend': AnalyticsService._get_optimization_trend(stores, start_date, end_date),
                'prompt_usage_trend': AnalyticsService._get_prompt_usage_trend(stores, start_date, end_date)
            }

            return {'dashboard': dashboard_data}, 200

        except Exception as e:
            return {'error': str(e)}, 500

    @staticmethod
    def _get_optimization_trend(
        stores: List[Store],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Helper method to get optimization trend data"""
        store_ids = [store.id for store in stores]
        trend_data = []
        
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            optimizations = Product.query.filter(
                Product.store_id.in_(store_ids),
                Product.last_optimized.between(current_date, next_date)
            ).count()
            
            trend_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'optimizations': optimizations
            })
            current_date = next_date
            
        return trend_data

    @staticmethod
    def _get_prompt_usage_trend(
        stores: List[Store],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Helper method to get prompt usage trend data"""
        store_ids = [store.id for store in stores]
        trend_data = []
        
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            prompts = Prompt.query.filter(
                Prompt.store_id.in_(store_ids),
                Prompt.created_at.between(current_date, next_date)
            ).count()
            
            trend_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'prompts': prompts
            })
            current_date = next_date
            
        return trend_data 