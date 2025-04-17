import React, { useState, useCallback } from 'react';
import {
  Card,
  FormLayout,
  Select,
  TextField,
  TextArea,
  Stack,
  Button,
  Banner,
} from '@shopify/polaris';

export function StorePromptForm({ onSubmit, availableOptions, isLoading }) {
  const [formData, setFormData] = useState({
    tone: 'professional',
    target_audience: 'general',
    writing_style: 'descriptive',
    description_length: 'medium',
    seo_keywords_focus: 'balanced',
    brand_voice: {
      personality: 'professional',
      emotion: 'neutral',
      formality: 'formal'
    },
    key_features: [],
    custom_instructions: '',
    example_description: ''
  });

  const handleChange = useCallback((field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  const handleBrandVoiceChange = useCallback((field, value) => {
    setFormData(prev => ({
      ...prev,
      brand_voice: {
        ...prev.brand_voice,
        [field]: value
      }
    }));
  }, []);

  const handleSubmit = useCallback(() => {
    onSubmit(formData);
  }, [formData, onSubmit]);

  return (
    <Card sectioned title="Prompt Settings">
      <Banner
        title="Customize Your Product Descriptions"
        status="info"
      >
        <p>Configure how you want your product descriptions to be generated. These settings can be changed later in the prompt dashboard.</p>
      </Banner>

      <div style={{ marginTop: '16px' }}>
        <FormLayout>
          <FormLayout.Group>
            <Select
              label="Tone of Voice"
              options={availableOptions.tones.map(tone => ({ label: tone, value: tone }))}
              value={formData.tone}
              onChange={value => handleChange('tone', value)}
              helpText="The overall tone for your product descriptions"
            />
            <Select
              label="Target Audience"
              options={availableOptions.target_audiences.map(audience => ({ label: audience, value: audience }))}
              value={formData.target_audience}
              onChange={value => handleChange('target_audience', value)}
              helpText="Who are your products primarily for?"
            />
          </FormLayout.Group>

          <FormLayout.Group>
            <Select
              label="Writing Style"
              options={availableOptions.writing_styles.map(style => ({ label: style, value: style }))}
              value={formData.writing_style}
              onChange={value => handleChange('writing_style', value)}
              helpText="How should the descriptions be written?"
            />
            <Select
              label="Description Length"
              options={availableOptions.description_lengths.map(length => ({ label: length, value: length }))}
              value={formData.description_length}
              onChange={value => handleChange('description_length', value)}
              helpText="Preferred length of product descriptions"
            />
          </FormLayout.Group>

          <Card sectioned title="Brand Voice">
            <FormLayout>
              <FormLayout.Group>
                <Select
                  label="Personality"
                  options={availableOptions.brand_voice_options.personality.map(p => ({ label: p, value: p }))}
                  value={formData.brand_voice.personality}
                  onChange={value => handleBrandVoiceChange('personality', value)}
                />
                <Select
                  label="Emotion"
                  options={availableOptions.brand_voice_options.emotion.map(e => ({ label: e, value: e }))}
                  value={formData.brand_voice.emotion}
                  onChange={value => handleBrandVoiceChange('emotion', value)}
                />
                <Select
                  label="Formality"
                  options={availableOptions.brand_voice_options.formality.map(f => ({ label: f, value: f }))}
                  value={formData.brand_voice.formality}
                  onChange={value => handleBrandVoiceChange('formality', value)}
                />
              </FormLayout.Group>
            </FormLayout>
          </Card>

          <TextArea
            label="Example Product Description"
            value={formData.example_description}
            onChange={value => handleChange('example_description', value)}
            helpText="Provide an example of how you'd like your descriptions to look"
          />

          <TextArea
            label="Custom Instructions"
            value={formData.custom_instructions}
            onChange={value => handleChange('custom_instructions', value)}
            helpText="Any specific instructions or requirements for your descriptions"
          />

          <Stack distribution="trailing">
            <Button primary onClick={handleSubmit} loading={isLoading}>
              Save Settings
            </Button>
          </Stack>
        </FormLayout>
      </div>
    </Card>
  );
} 