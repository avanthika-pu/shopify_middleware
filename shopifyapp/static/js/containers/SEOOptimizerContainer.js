import React, { useState } from 'react';
import { useToast } from '@shopify/app-bridge-react';
import { SEOOptimizer } from '../components/SEOOptimizer';
import { useAPI } from '../hooks/useAPI';

export function SEOOptimizerContainer({ product, storeId, onUpdate }) {
  const [isOptimizing, setIsOptimizing] = useState(false);
  const { show: showToast } = useToast();
  const api = useAPI();

  const handleOptimize = async (preferences) => {
    try {
      setIsOptimizing(true);
      
      const response = await api.post(
        `/api/stores/${storeId}/products/${product.id}/optimize`,
        preferences
      );

      if (response.data.product) {
        onUpdate(response.data.product);
        showToast('Product description optimized successfully');
      }
    } catch (error) {
      console.error('Optimization failed:', error);
      showToast('Failed to optimize product description', { isError: true });
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <SEOOptimizer
      product={product}
      onOptimize={handleOptimize}
      isOptimizing={isOptimizing}
    />
  );
} 