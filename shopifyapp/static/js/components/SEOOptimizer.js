import React, { useState } from 'react';
import {
  Card,
  Button,
  TextContainer,
  Stack,
  Banner,
  SkeletonBodyText,
  Modal,
  TextArea,
  Select,
} from '@shopify/polaris';

export function SEOOptimizer({ product, onOptimize, isOptimizing }) {
  const [showPreview, setShowPreview] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');
  const [selectedTone, setSelectedTone] = useState('professional');

  const handleOptimize = async () => {
    const preferences = {
      tone: selectedTone,
      custom_prompt: customPrompt || undefined,
    };
    await onOptimize(preferences);
  };

  const toneOptions = [
    { label: 'Professional', value: 'professional' },
    { label: 'Casual', value: 'casual' },
    { label: 'Friendly', value: 'friendly' },
    { label: 'Luxury', value: 'luxury' },
    { label: 'Technical', value: 'technical' },
  ];

  return (
    <Card sectioned>
      <Stack vertical spacing="tight">
        <TextContainer>
          <h2>SEO Optimization</h2>
          <p>
            Optimize your product description using AI to improve SEO ranking and conversion rates.
          </p>
        </TextContainer>

        <Select
          label="Tone of Voice"
          options={toneOptions}
          value={selectedTone}
          onChange={setSelectedTone}
        />

        <TextArea
          label="Custom Instructions (Optional)"
          value={customPrompt}
          onChange={setCustomPrompt}
          placeholder="Add any specific requirements or keywords to include..."
        />

        <Stack distribution="trailing">
          <Button onClick={() => setShowPreview(true)} disabled={!product.optimized_description}>
            Preview Optimization
          </Button>
          <Button primary onClick={handleOptimize} loading={isOptimizing}>
            Optimize Description
          </Button>
        </Stack>

        {isOptimizing && (
          <Banner status="info">
            <p>Generating optimized description...</p>
            <SkeletonBodyText lines={3} />
          </Banner>
        )}

        <Modal
          open={showPreview}
          onClose={() => setShowPreview(false)}
          title="Optimized Description Preview"
          primaryAction={{
            content: 'Close',
            onAction: () => setShowPreview(false),
          }}
        >
          <Modal.Section>
            <Stack vertical spacing="tight">
              <TextContainer>
                <h3>Original Description</h3>
                <div dangerouslySetInnerHTML={{ __html: product.original_description }} />
              </TextContainer>

              <TextContainer>
                <h3>Optimized Description</h3>
                <div dangerouslySetInnerHTML={{ __html: product.optimized_description }} />
              </TextContainer>
            </Stack>
          </Modal.Section>
        </Modal>
      </Stack>
    </Card>
  );
} 