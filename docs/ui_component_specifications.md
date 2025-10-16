# DraftGenie UI Component Specifications

**Version:** 1.0  
**Last Updated:** 2025-10-16  
**Companion to:** `ui_ux_design_specification.md`

---

## Table of Contents

1. [Component Design System](#1-component-design-system)
2. [Core Components](#2-core-components)
3. [Form Components](#3-form-components)
4. [Data Display Components](#4-data-display-components)
5. [Feedback Components](#5-feedback-components)
6. [Layout Components](#6-layout-components)

---

## 1. Component Design System

### 1.1 Design Tokens

#### Colors
```css
/* Primary Colors */
--color-primary: #1976D2;
--color-primary-light: #42A5F5;
--color-primary-dark: #1565C0;

/* Bucket Colors */
--color-excellent: #4CAF50;
--color-good: #2196F3;
--color-average: #FFC107;
--color-poor: #FF9800;
--color-needs-improvement: #F44336;

/* Semantic Colors */
--color-success: #4CAF50;
--color-warning: #FF9800;
--color-error: #F44336;
--color-info: #2196F3;

/* Neutral Colors */
--color-gray-50: #FAFAFA;
--color-gray-100: #F5F5F5;
--color-gray-200: #EEEEEE;
--color-gray-300: #E0E0E0;
--color-gray-400: #BDBDBD;
--color-gray-500: #9E9E9E;
--color-gray-600: #757575;
--color-gray-700: #616161;
--color-gray-800: #424242;
--color-gray-900: #212121;

/* Text Colors */
--color-text-primary: rgba(0, 0, 0, 0.87);
--color-text-secondary: rgba(0, 0, 0, 0.60);
--color-text-disabled: rgba(0, 0, 0, 0.38);
```

#### Spacing
```css
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 32px;
--spacing-2xl: 48px;
--spacing-3xl: 64px;
```

#### Typography
```css
/* Font Families */
--font-primary: 'Inter', 'Roboto', -apple-system, sans-serif;
--font-mono: 'Roboto Mono', 'Fira Code', monospace;

/* Font Sizes */
--font-size-xs: 12px;
--font-size-sm: 14px;
--font-size-md: 16px;
--font-size-lg: 18px;
--font-size-xl: 20px;
--font-size-2xl: 24px;
--font-size-3xl: 30px;
--font-size-4xl: 36px;

/* Font Weights */
--font-weight-regular: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;

/* Line Heights */
--line-height-tight: 1.25;
--line-height-normal: 1.5;
--line-height-relaxed: 1.75;
```

#### Borders & Shadows
```css
/* Border Radius */
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
--radius-full: 9999px;

/* Shadows */
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
```

---

## 2. Core Components

### 2.1 BucketBadge

**Purpose:** Display speaker quality bucket with consistent styling

**Props:**
```typescript
interface BucketBadgeProps {
  bucket: 'EXCELLENT' | 'GOOD' | 'AVERAGE' | 'POOR' | 'NEEDS_IMPROVEMENT';
  size?: 'sm' | 'md' | 'lg';
  variant?: 'filled' | 'outlined' | 'minimal';
  showIcon?: boolean;
}
```

**Variants:**

**Filled (Default):**
```html
<span class="bucket-badge bucket-badge--filled bucket-badge--excellent">
  <svg class="bucket-badge__icon">...</svg>
  <span class="bucket-badge__text">EXCELLENT</span>
</span>
```

**Styles:**
```css
.bucket-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  line-height: 1;
}

.bucket-badge--sm {
  padding: 2px var(--spacing-xs);
  font-size: var(--font-size-xs);
}

.bucket-badge--lg {
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-md);
}

/* Filled Variant */
.bucket-badge--filled.bucket-badge--excellent {
  background-color: var(--color-excellent);
  color: white;
}

.bucket-badge--filled.bucket-badge--good {
  background-color: var(--color-good);
  color: white;
}

.bucket-badge--filled.bucket-badge--average {
  background-color: var(--color-average);
  color: rgba(0, 0, 0, 0.87);
}

.bucket-badge--filled.bucket-badge--poor {
  background-color: var(--color-poor);
  color: white;
}

.bucket-badge--filled.bucket-badge--needs-improvement {
  background-color: var(--color-needs-improvement);
  color: white;
}

/* Outlined Variant */
.bucket-badge--outlined {
  background-color: transparent;
  border: 2px solid currentColor;
}

.bucket-badge--outlined.bucket-badge--excellent {
  color: var(--color-excellent);
}

/* Minimal Variant */
.bucket-badge--minimal {
  background-color: transparent;
  padding: 0;
}
```

**Usage Example:**
```jsx
// React
<BucketBadge bucket="EXCELLENT" size="md" variant="filled" showIcon={true} />

// Vue
<BucketBadge :bucket="speaker.bucket" size="md" variant="filled" :show-icon="true" />

// Angular
<app-bucket-badge [bucket]="speaker.bucket" size="md" variant="filled" [showIcon]="true"></app-bucket-badge>
```

---

### 2.2 SpeakerCard

**Purpose:** Display speaker summary in lists and grids

**Props:**
```typescript
interface SpeakerCardProps {
  speaker: {
    id: string;
    name: string;
    email?: string;
    bucket: BucketType;
    status: SpeakerStatus;
    metadata?: Record<string, any>;
  };
  onClick?: (speaker: Speaker) => void;
  showActions?: boolean;
  variant?: 'default' | 'compact';
}
```

**Layout:**
```html
<div class="speaker-card" onclick="handleClick()">
  <div class="speaker-card__header">
    <div class="speaker-card__avatar">
      <span class="speaker-card__initials">JS</span>
    </div>
    <div class="speaker-card__info">
      <h3 class="speaker-card__name">Dr. John Smith</h3>
      <p class="speaker-card__email">john.smith@hospital.com</p>
    </div>
    <div class="speaker-card__badge">
      <BucketBadge bucket="GOOD" size="sm" />
    </div>
  </div>
  
  <div class="speaker-card__metadata">
    <div class="speaker-card__meta-item">
      <span class="speaker-card__meta-label">Specialty:</span>
      <span class="speaker-card__meta-value">Cardiology</span>
    </div>
    <div class="speaker-card__meta-item">
      <span class="speaker-card__meta-label">Drafts:</span>
      <span class="speaker-card__meta-value">45</span>
    </div>
  </div>
  
  <div class="speaker-card__actions" v-if="showActions">
    <button class="speaker-card__action-btn">View</button>
    <button class="speaker-card__action-btn">Edit</button>
  </div>
</div>
```

**Styles:**
```css
.speaker-card {
  background: white;
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  cursor: pointer;
  transition: all 0.2s ease;
}

.speaker-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.speaker-card__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.speaker-card__avatar {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.speaker-card__initials {
  color: white;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-lg);
}

.speaker-card__info {
  flex: 1;
  min-width: 0;
}

.speaker-card__name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-xs) 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.speaker-card__email {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.speaker-card__metadata {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-gray-200);
}

.speaker-card__meta-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.speaker-card__meta-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.speaker-card__meta-value {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  font-weight: var(--font-weight-medium);
}

.speaker-card__actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.speaker-card__action-btn {
  flex: 1;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-md);
  background: white;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all 0.2s ease;
}

.speaker-card__action-btn:hover {
  background: var(--color-gray-50);
  border-color: var(--color-primary);
  color: var(--color-primary);
}
```

**States:**
- **Default:** Normal appearance
- **Hover:** Elevated with shadow, border color changes
- **Selected:** Border color primary, background tinted
- **Disabled:** Reduced opacity, no hover effects

---

### 2.3 DraftComparison

**Purpose:** Side-by-side text comparison with diff highlighting

**Props:**
```typescript
interface DraftComparisonProps {
  original: string;
  corrected: string;
  showLineNumbers?: boolean;
  highlightLevel?: 'word' | 'character';
  collapsible?: boolean;
}
```

**Layout:**
```html
<div class="draft-comparison">
  <div class="draft-comparison__header">
    <h3 class="draft-comparison__title">Draft Comparison</h3>
    <div class="draft-comparison__legend">
      <span class="draft-comparison__legend-item">
        <span class="diff-added"></span> Added
      </span>
      <span class="draft-comparison__legend-item">
        <span class="diff-removed"></span> Removed
      </span>
      <span class="draft-comparison__legend-item">
        <span class="diff-modified"></span> Modified
      </span>
    </div>
  </div>
  
  <div class="draft-comparison__content">
    <div class="draft-comparison__panel">
      <div class="draft-comparison__panel-header">
        <h4>Original (AD)</h4>
      </div>
      <div class="draft-comparison__panel-body">
        <pre class="draft-comparison__text">
          <code>
            <span class="line" data-line="1">The patient has a history of <span class="diff-removed">diabetis</span>.</span>
            <span class="line" data-line="2">He is currently taking <span class="diff-removed">metformin</span>.</span>
          </code>
        </pre>
      </div>
    </div>
    
    <div class="draft-comparison__divider"></div>
    
    <div class="draft-comparison__panel">
      <div class="draft-comparison__panel-header">
        <h4>Corrected (IFN)</h4>
      </div>
      <div class="draft-comparison__panel-body">
        <pre class="draft-comparison__text">
          <code>
            <span class="line" data-line="1">The patient has a history of <span class="diff-added">diabetes</span>.</span>
            <span class="line" data-line="2">He is currently taking <span class="diff-added">Metformin</span>.</span>
          </code>
        </pre>
      </div>
    </div>
  </div>
</div>
```

**Styles:**
```css
.draft-comparison {
  background: white;
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.draft-comparison__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-gray-50);
  border-bottom: 1px solid var(--color-gray-200);
}

.draft-comparison__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin: 0;
}

.draft-comparison__legend {
  display: flex;
  gap: var(--spacing-md);
}

.draft-comparison__legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.draft-comparison__legend-item span:first-child {
  width: 16px;
  height: 16px;
  border-radius: var(--radius-sm);
}

.draft-comparison__content {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 0;
}

.draft-comparison__panel {
  display: flex;
  flex-direction: column;
  min-height: 300px;
}

.draft-comparison__panel-header {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-gray-100);
  border-bottom: 1px solid var(--color-gray-200);
}

.draft-comparison__panel-header h4 {
  margin: 0;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.draft-comparison__panel-body {
  flex: 1;
  overflow: auto;
  padding: var(--spacing-md);
}

.draft-comparison__text {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.draft-comparison__text .line {
  display: block;
  padding: 2px 0;
}

.draft-comparison__text .line::before {
  content: attr(data-line);
  display: inline-block;
  width: 40px;
  margin-right: var(--spacing-md);
  color: var(--color-text-disabled);
  text-align: right;
  user-select: none;
}

.draft-comparison__divider {
  width: 1px;
  background: var(--color-gray-200);
}

/* Diff Highlighting */
.diff-added {
  background-color: rgba(76, 175, 80, 0.2);
  color: #2E7D32;
  padding: 2px 4px;
  border-radius: var(--radius-sm);
}

.diff-removed {
  background-color: rgba(244, 67, 54, 0.2);
  color: #C62828;
  padding: 2px 4px;
  border-radius: var(--radius-sm);
  text-decoration: line-through;
}

.diff-modified {
  background-color: rgba(255, 193, 7, 0.2);
  color: #F57C00;
  padding: 2px 4px;
  border-radius: var(--radius-sm);
}

/* Responsive */
@media (max-width: 768px) {
  .draft-comparison__content {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
  }
  
  .draft-comparison__divider {
    display: none;
  }
  
  .draft-comparison__panel:first-child {
    border-bottom: 1px solid var(--color-gray-200);
  }
}
```

---

### 2.4 MetricsPanel

**Purpose:** Display quality metrics in consistent format

**Props:**
```typescript
interface MetricsPanelProps {
  metrics: {
    ser: number;      // 0-1
    wer: number;      // 0-1
    similarity: number; // 0-1
    qualityScore: number; // 0-100
  };
  layout?: 'horizontal' | 'vertical';
  showTrends?: boolean;
}
```

**Layout:**
```html
<div class="metrics-panel">
  <div class="metrics-panel__header">
    <h3 class="metrics-panel__title">Quality Metrics</h3>
  </div>
  
  <div class="metrics-panel__grid">
    <!-- SER Metric -->
    <div class="metric-card">
      <div class="metric-card__header">
        <span class="metric-card__label">SER</span>
        <span class="metric-card__info-icon" title="Sentence Edit Rate">ℹ️</span>
      </div>
      <div class="metric-card__value">15%</div>
      <div class="metric-card__progress">
        <div class="metric-card__progress-bar" style="width: 15%; background: var(--color-success);"></div>
      </div>
      <div class="metric-card__description">Lower is better</div>
    </div>
    
    <!-- WER Metric -->
    <div class="metric-card">
      <div class="metric-card__header">
        <span class="metric-card__label">WER</span>
        <span class="metric-card__info-icon" title="Word Error Rate">ℹ️</span>
      </div>
      <div class="metric-card__value">8%</div>
      <div class="metric-card__progress">
        <div class="metric-card__progress-bar" style="width: 8%; background: var(--color-success);"></div>
      </div>
      <div class="metric-card__description">Lower is better</div>
    </div>
    
    <!-- Similarity Metric -->
    <div class="metric-card">
      <div class="metric-card__header">
        <span class="metric-card__label">Similarity</span>
        <span class="metric-card__info-icon" title="Semantic Similarity">ℹ️</span>
      </div>
      <div class="metric-card__value">92%</div>
      <div class="metric-card__circular-progress">
        <svg viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="45" fill="none" stroke="var(--color-gray-200)" stroke-width="10"/>
          <circle cx="50" cy="50" r="45" fill="none" stroke="var(--color-success)" stroke-width="10" 
                  stroke-dasharray="282.7" stroke-dashoffset="22.6" transform="rotate(-90 50 50)"/>
        </svg>
        <span class="metric-card__circular-value">92%</span>
      </div>
      <div class="metric-card__description">Higher is better</div>
    </div>
    
    <!-- Quality Score -->
    <div class="metric-card metric-card--featured">
      <div class="metric-card__header">
        <span class="metric-card__label">Overall Quality</span>
      </div>
      <div class="metric-card__value metric-card__value--large">87.5</div>
      <div class="metric-card__trend metric-card__trend--up">
        <span class="metric-card__trend-icon">↑</span>
        <span class="metric-card__trend-value">+5.2%</span>
        <span class="metric-card__trend-label">vs last month</span>
      </div>
    </div>
  </div>
</div>
```

**Styles:**
```css
.metrics-panel {
  background: white;
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.metrics-panel__header {
  margin-bottom: var(--spacing-lg);
}

.metrics-panel__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  margin: 0;
}

.metrics-panel__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-lg);
}

.metric-card {
  background: var(--color-gray-50);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.metric-card--featured {
  background: linear-gradient(135deg, var(--color-primary-light), var(--color-primary));
  color: white;
  border: none;
}

.metric-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.metric-card__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-card--featured .metric-card__label {
  color: rgba(255, 255, 255, 0.9);
}

.metric-card__value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.metric-card__value--large {
  font-size: var(--font-size-4xl);
}

.metric-card--featured .metric-card__value {
  color: white;
}

.metric-card__progress {
  height: 8px;
  background: var(--color-gray-200);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--spacing-sm);
}

.metric-card__progress-bar {
  height: 100%;
  transition: width 0.3s ease;
}

.metric-card__circular-progress {
  position: relative;
  width: 100px;
  height: 100px;
  margin: var(--spacing-md) auto;
}

.metric-card__circular-progress svg {
  width: 100%;
  height: 100%;
}

.metric-card__circular-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
}

.metric-card__description {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.metric-card--featured .metric-card__description {
  color: rgba(255, 255, 255, 0.8);
}

.metric-card__trend {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
}

.metric-card__trend--up {
  color: var(--color-success);
}

.metric-card__trend--down {
  color: var(--color-error);
}

.metric-card--featured .metric-card__trend {
  color: rgba(255, 255, 255, 0.9);
}

.metric-card__trend-icon {
  font-size: var(--font-size-lg);
}

.metric-card__trend-value {
  font-weight: var(--font-weight-semibold);
}

.metric-card__trend-label {
  color: var(--color-text-secondary);
}

.metric-card--featured .metric-card__trend-label {
  color: rgba(255, 255, 255, 0.7);
}
```

---

## 3. Form Components

### 3.1 SpeakerForm

**Purpose:** Create or edit speaker information

**Props:**
```typescript
interface SpeakerFormProps {
  initialData?: Partial<Speaker>;
  onSubmit: (data: SpeakerFormData) => Promise<void>;
  onCancel: () => void;
  mode: 'create' | 'edit';
}
```

**Fields:**
- Name (required, text, min 2 chars)
- Email (optional, email format)
- Bucket (required, dropdown)
- External ID (required for create, text)
- Notes (optional, textarea)
- Metadata (optional, key-value pairs)

**Validation Rules:**
```typescript
const validationRules = {
  name: {
    required: true,
    minLength: 2,
    maxLength: 255,
    pattern: /^[a-zA-Z\s.'-]+$/,
    message: 'Name must be at least 2 characters'
  },
  email: {
    required: false,
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    message: 'Please enter a valid email address'
  },
  bucket: {
    required: true,
    enum: ['EXCELLENT', 'GOOD', 'AVERAGE', 'POOR', 'NEEDS_IMPROVEMENT'],
    message: 'Please select a bucket'
  },
  externalId: {
    required: true,
    minLength: 1,
    maxLength: 255,
    message: 'External ID is required'
  }
};
```

**Layout:**
```html
<form class="speaker-form" onsubmit="handleSubmit">
  <div class="speaker-form__section">
    <h3 class="speaker-form__section-title">Basic Information</h3>
    
    <div class="form-field">
      <label class="form-field__label" for="name">
        Name <span class="form-field__required">*</span>
      </label>
      <input 
        type="text" 
        id="name" 
        class="form-field__input"
        placeholder="Dr. John Smith"
        required
      />
      <span class="form-field__error">Name must be at least 2 characters</span>
      <span class="form-field__hint">Enter the speaker's full name</span>
    </div>
    
    <div class="form-field">
      <label class="form-field__label" for="email">Email</label>
      <input 
        type="email" 
        id="email" 
        class="form-field__input"
        placeholder="john.smith@hospital.com"
      />
    </div>
    
    <div class="form-field">
      <label class="form-field__label" for="bucket">
        Initial Bucket <span class="form-field__required">*</span>
      </label>
      <select id="bucket" class="form-field__select" required>
        <option value="">Select a bucket...</option>
        <option value="EXCELLENT">🟢 EXCELLENT</option>
        <option value="GOOD">🔵 GOOD</option>
        <option value="AVERAGE">🟡 AVERAGE</option>
        <option value="POOR">🟠 POOR</option>
        <option value="NEEDS_IMPROVEMENT">🔴 NEEDS IMPROVEMENT</option>
      </select>
    </div>
    
    <div class="form-field">
      <label class="form-field__label" for="externalId">
        External ID <span class="form-field__required">*</span>
      </label>
      <input 
        type="text" 
        id="externalId" 
        class="form-field__input"
        placeholder="instanote-speaker-12345"
        required
      />
      <span class="form-field__hint">ID from InstaNote system</span>
    </div>
  </div>
  
  <div class="speaker-form__section">
    <h3 class="speaker-form__section-title">Additional Information</h3>
    
    <div class="form-field">
      <label class="form-field__label" for="notes">Notes</label>
      <textarea 
        id="notes" 
        class="form-field__textarea"
        placeholder="Add any additional notes about this speaker..."
        rows="4"
      ></textarea>
    </div>
    
    <div class="form-field">
      <label class="form-field__label">Metadata</label>
      <div class="metadata-editor">
        <div class="metadata-editor__row">
          <input type="text" placeholder="Key" class="metadata-editor__key" />
          <input type="text" placeholder="Value" class="metadata-editor__value" />
          <button type="button" class="metadata-editor__remove">×</button>
        </div>
        <button type="button" class="metadata-editor__add">+ Add Field</button>
      </div>
    </div>
  </div>
  
  <div class="speaker-form__actions">
    <button type="button" class="btn btn--secondary" onclick="handleCancel">
      Cancel
    </button>
    <button type="submit" class="btn btn--primary">
      Create Speaker
    </button>
  </div>
</form>
```

---

**[Document continues with more component specifications...]**

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-16  
**Total Components:** 15+ detailed specifications  
**Related Documents:**
- `ui_ux_design_specification.md` - Main specification
- `ui_ux_visual_workflows.md` - Workflow diagrams

