---
name: Vera Studio Clinical Commerce
colors:
  surface: '#f7f9ff'
  surface-dim: '#d1dbe9'
  surface-bright: '#f7f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#edf4ff'
  surface-container: '#e5effd'
  surface-container-high: '#dfe9f7'
  surface-container-highest: '#d9e3f2'
  on-surface: '#131c26'
  on-surface-variant: '#414848'
  inverse-surface: '#28313c'
  inverse-on-surface: '#e8f1ff'
  outline: '#717878'
  outline-variant: '#c1c8c7'
  surface-tint: '#426464'
  primary: '#002424'
  on-primary: '#ffffff'
  primary-container: '#163a3a'
  on-primary-container: '#80a4a3'
  inverse-primary: '#a9cdcd'
  secondary: '#526600'
  on-secondary: '#ffffff'
  secondary-container: '#c9f236'
  on-secondary-container: '#576c00'
  tertiary: '#430900'
  on-tertiary: '#ffffff'
  tertiary-container: '#691300'
  on-tertiary-container: '#ff714e'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c4eae9'
  primary-fixed-dim: '#a9cdcd'
  on-primary-fixed: '#002020'
  on-primary-fixed-variant: '#2a4c4c'
  secondary-fixed: '#c9f236'
  secondary-fixed-dim: '#aed50d'
  on-secondary-fixed: '#171e00'
  on-secondary-fixed-variant: '#3d4d00'
  tertiary-fixed: '#ffdad2'
  tertiary-fixed-dim: '#ffb4a2'
  on-tertiary-fixed: '#3c0700'
  on-tertiary-fixed-variant: '#8a1c00'
  background: '#f7f9ff'
  on-background: '#131c26'
  surface-variant: '#d9e3f2'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 3rem
    fontWeight: '700'
    lineHeight: 3.5rem
    letterSpacing: -0.03em
  display-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 2rem
    fontWeight: '700'
    lineHeight: 2.5rem
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 2rem
    fontWeight: '600'
    lineHeight: 2.5rem
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 2rem
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 2rem
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 1.125rem
    fontWeight: '600'
    lineHeight: 1.625rem
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.125rem
    fontWeight: '400'
    lineHeight: 1.75rem
    letterSpacing: 0em
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.9375rem
    fontWeight: '400'
    lineHeight: 1.5rem
    letterSpacing: 0em
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.8125rem
    fontWeight: '400'
    lineHeight: 1.25rem
    letterSpacing: 0.005em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.875rem
    fontWeight: '600'
    lineHeight: 1.25rem
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.75rem
    fontWeight: '600'
    lineHeight: 1rem
    letterSpacing: 0.02em
  tabular-data:
    fontFamily: JetBrains Mono
    fontSize: 0.875rem
    fontWeight: '500'
    lineHeight: 1.25rem
    letterSpacing: 0.02em
  tabular-sm:
    fontFamily: JetBrains Mono
    fontSize: 0.75rem
    fontWeight: '500'
    lineHeight: 1rem
    letterSpacing: 0.03em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system establishes an editorial, tactile intersection between warm Indian retail commerce and meticulous clinical workflows. Designed for dental clinical teams managing high-volume patient engagement, retention funnels, and commerce triggers, the aesthetic departs from cold, generic healthcare SaaS through warm paper tones, deep inks, and vibrant energetic accents.

The design movement synthesizes **Warm Editorial Minimalism** with **Structured Tactical Commerce**:
- **Warm Editorial Baseline:** Employs parchment-like warmth (`#F6F2EA` and `#FFFCF7`) rather than antiseptic blue-whites, lending tactile hospitality to operational workspaces.
- **Clinical Precision:** Crisp hairline dividers, strict tabular alignment, and disciplined monospaced numerical anchors ensure high-density treatment plans, recall schedules, and patient cohorts remain unambiguous.
- **Electric Commerce Vibrancy:** Strategic strikes of energetic lime (`#C8F135`) denote trigger events and high-priority action states, balanced by authoritative merchant navy and soothing sage.

## Colors

The palette balances warm organic substrates against high-legibility inks and purposeful functional status tones:

- **Canvas & Surface Base:**
  - `canvas-default`: `#F6F2EA` (Warm paper background for primary page backdrops)
  - `surface-elevated`: `#FFFCF7` (Chalk surface for cards, modals, and operational sheets)
  - `surface-sunken`: `#ECE5DA` (Recessed wells, inactive tabular rows)
  - `border-hairline`: `#E4DDD2` (Crisp 1px boundary lines separating treatment and cohort columns)

- **Ink Typography:**
  - `ink-primary`: `#0F1C2E` (Merchant Navy; authoritative body text, primary values, and headlines)
  - `ink-secondary`: `#5C6672` (Subtle metadata, helper prompts, timestamp indicators)
  - `ink-disabled`: `#A39E93` (Deactivated operations and disabled input values)

- **Functional Accents & Domain Taxonomies:**
  - `accent-trigger`: `#C8F135` (High-contrast energetic lime; strictly requires `#0F1C2E` ink for foreground text)
  - `clinical-teal`: `#163A3A` (Deep teal-ink; anchors clinical primary navigation, primary buttons, and treatment states)
  - `category-sage`: `#7A8F6A` (Represents preventative maintenance, oral care categories, and routine hygiene cohorts)
  - `customer-coral`: `#D97857` (Muted coral; patient identity badges and communication statuses)
  - `alert-critical`: `#E85D3B` (Vibrant coral; treatment drops, overdue appointments, critical cancellations)
  - `state-success`: `#2F6F4E` (Soft green; completed procedures, settled ledger balances, verified recalls)

## Typography

The typographic hierarchy establishes distinct zones of structural communication:
- **Display & Headings:** `Space Grotesk` introduces modern geometric cadence with intentional ink traps and assertive letterforms, nodding to high-end contemporary retail and brand identity.
- **Body & Operational Copy:** `Plus Jakarta Sans` delivers warm, humanist geometry that maintains exceptional legibility during intense clinical records review, treatment plan audits, and messaging sequence setup.
- **Clinical Data & Metrics:** `JetBrains Mono` handles all currency amounts, patient MRNs (Medical Record Numbers), procedural billing codes, tooth notations, and timestamps with tabular lining figures to ensure zero vertical jitter across operational tables.

## Layout & Spacing

A strict 8pt structural rhythm governs spacing and alignment. All content conforms to an adaptive layout engine tailored for split clinical-receptionist tablet stations and full-screen clinic workstations:

- **Desktop (1200px+):** 12-column layout with 24px (`1.5rem`) gutters and 32px (`2rem`) margins. Main clinic workbench leverages a persistent 280px left rail, a fluid dynamic campaign workspace, and an optional 360px contextual patient inspection drawer.
- **Tablet / Operatory Viewport (768px - 1199px):** 8-column layout with 20px gutters and 24px margins. Navigation condenses to an icon-dock rail; table columns drop lower-priority analytics in favor of direct procedural action buttons.
- **Mobile Handheld (320px - 767px):** 4-column layout with 16px (`1rem`) gutters and 16px (`1rem`) page margins. Secondary action panels collapse into full-width bottom sheets.

## Elevation & Depth

This system avoids synthetic blur drop-shadows, utilizing tactile layered surfaces punctuated by hairline ink boundaries:

- **Surface Tiers:**
  - **Ground Floor:** `#F6F2EA` (Paper canvas).
  - **Card Layer:** `#FFFCF7` bordered by 1px solid `#E4DDD2`.
  - **Selected / Active Layer:** `#FFFCF7` outlined by 1.5px solid `#163A3A`.
  - **Overlay / Modal Layer:** `#FFFCF7` with a crisp, directional hairline cast shadow: `0 4px 0 0 rgba(15, 28, 46, 0.05), 0 16px 32px 0 rgba(15, 28, 46, 0.08)`.
- **Dividers & Gridlines:** Never exceed 1px stroke. Dividers employ `#E4DDD2` to reinforce a clean ledger-like physical ledger feel.

## Shapes

The geometric form system delivers tailored corner articulation based on component hierarchy:
- **Base Components (Inputs, Chips, Table Rows):** Fixed at `10px` (`0.625rem`) radius for crisp touch targets that remain clinical without appearing harsh.
- **Cards & Primary Modules:** Standardized to `14px` (`0.875rem`) radius, balancing soft paper handling with spatial order.
- **Modals, Drawers & Trigger Banners:** Generous `18px` (`1.125rem`) radius, framing multi-step campaign flows and patient records.
- **Avatars & Badge Indicators:** Circular (Full pill / 9999px).

## Components

### Buttons
- **Trigger / Primary Commerce Action:** Solid `#C8F135` surface with `#0F1C2E` ink, medium weight `Space Grotesk` or `Plus Jakarta Sans`, 10px corner radius. On hover, slightly deepens to `#B8DF24`.
- **Clinical Primary:** Solid `#163A3A` with `#FFFCF7` white chalk ink. High visual weight for approving care pathways or saving clinical chart notes.
- **Secondary Hairline:** `#FFFCF7` chalk surface with 1px border `#E4DDD2` and `#0F1C2E` ink. Hover shifts background to `#F6F2EA`.
- **Destructive:** Coral tinted border `#E85D3B` on `#FFFCF7`, text `#E85D3B`.

### Chips & Badges
- **Status Pills:** 6px vertical padding, 10px horizontal padding, full radius.
  - *Trigger Active:* `#C8F135` background with `#0F1C2E` typography.
  - *Preventative Recall:* `#7A8F6A` with 12% tint background and solid `#2D3A25` ink.
  - *Procedure Due:* `#D97857` with 14% tint background and `#592718` ink.
  - *Ledger Settled:* `#2F6F4E` with 12% tint background and `#143825` ink.

### Input Fields & Controls
- **Field Canvas:** `#FFFCF7` background, 1px `#E4DDD2` border, 10px radius, 12px 16px internal padding.
- **Focus State:** 1.5px solid `#163A3A`, zero artificial neon glow rings.
- **Checkboxes & Radios:** 18px square (checkbox, 4px radius) or 18px circle (radio). Active state fills with `#163A3A` displaying a clean checkmark or inner dot in chalk `#FFFCF7`.

### Cards & Workflow Modules
- Surface: `#FFFCF7` framed with 1px `#E4DDD2`. 14px radius.
- Padding: 16px (`1rem`) on compact views, 24px (`1.5rem`) on full-width treatment modules.
- Header separator: 1px hairline horizontal divider in `#E4DDD2`.

### Clinical Workflow Timeline & Recall Nodes
- Vertical stepper connected by a continuous 1.5px solid `#E4DDD2` rule.
- Node indicators: 24px round markers. Completed steps show `#2F6F4E` fills with white icons; impending automation steps display `#C8F135` with dark ink centered pips.