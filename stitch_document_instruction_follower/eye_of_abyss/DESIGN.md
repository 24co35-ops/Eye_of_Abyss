---
name: Eye of Abyss
colors:
  surface: '#14121b'
  surface-dim: '#14121b'
  surface-bright: '#3b3842'
  surface-container-lowest: '#0f0d16'
  surface-container-low: '#1c1a24'
  surface-container: '#211e28'
  surface-container-high: '#2b2933'
  surface-container-highest: '#36333e'
  on-surface: '#e6e0ee'
  on-surface-variant: '#d6c4ac'
  inverse-surface: '#e6e0ee'
  inverse-on-surface: '#322f39'
  outline: '#9f8e79'
  outline-variant: '#514533'
  surface-tint: '#ffba44'
  primary: '#ffc56c'
  on-primary: '#442c00'
  primary-container: '#f0a500'
  on-primary-container: '#5f3f00'
  inverse-primary: '#805600'
  secondary: '#c7bfff'
  on-secondary: '#2c009e'
  secondary-container: '#410bd7'
  on-secondary-container: '#b5abff'
  tertiary: '#ffc0b9'
  on-tertiary: '#680007'
  tertiary-container: '#ff978e'
  on-tertiary-container: '#91000e'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffddaf'
  primary-fixed-dim: '#ffba44'
  on-primary-fixed: '#281800'
  on-primary-fixed-variant: '#614000'
  secondary-fixed: '#e5deff'
  secondary-fixed-dim: '#c7bfff'
  on-secondary-fixed: '#180064'
  on-secondary-fixed-variant: '#410bd7'
  tertiary-fixed: '#ffdad6'
  tertiary-fixed-dim: '#ffb4ac'
  on-tertiary-fixed: '#410003'
  on-tertiary-fixed-variant: '#93000f'
  background: '#14121b'
  on-background: '#e6e0ee'
  surface-variant: '#36333e'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 22px
    fontWeight: '500'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0em
  title-md:
    fontFamily: Space Grotesk
    fontSize: 15px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  body-md:
    fontFamily: Space Grotesk
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0.01em
  body-sm:
    fontFamily: Space Grotesk
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.02em
  data-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: -0.02em
  data-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: -0.01em
  data-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.02em
  label-xs:
    fontFamily: Space Grotesk
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 12px
    letterSpacing: 0.08em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 16px
  margin: 24px
  space-xs: 4px
  space-sm: 8px
  space-md: 16px
  space-lg: 24px
  space-xl: 32px
---

## Brand & Style

This design system establishes an operational workspace for law enforcement cybercrime units, financial intelligence officers, and state-level cyber investigators. Its character reflects calm, immovable institutional authority under intense operational friction. The visual metaphor hinges on profound darkness penetrated by a single, unwavering point of amber-gold intelligence: the gaze that does not flinch.

The aesthetic fuses **Precision Brutalism** with **Instrumental Minimalism**:
- Surfaces are architectural, grounded in deep violet-black tones rather than synthetic pure blacks.
- Information density is exceptionally high; every pixel, border, and metric conveys forensic relevance.
- Visual noise is systematically purged. Decorative gradients, holographic skeuomorphism, and generic neon hacker cliches (such as cyan terminal glows or scanline textures) are forbidden.
- Authority is established through disciplined typographic cadence, crisp structural borders, and purposeful contrast.

## Colors

The palette is engineered for prolonged operational focus in darkened command centers and forensic workstations, eliminating optical fatigue while enforcing unambiguous hierarchy.

### Core Tonal Palette
- **Background (Abyss)** (`#0D0B14`): The foundational canvas. A deep, cold violet-black that retains spatial presence without clipping into dead black (`#000000`).
- **Surface (Void)** (`#13111E`): Used for primary containment zones, navigation backdrops, toolbars, and main structural panels.
- **Card Surface (Shadow)** (`#1C1929`): Used for nested modules, metric tiles, table rows, and form inputs.
- **Structural Border (Mist)** (`#2A2640`): 1px structural outlines separating distinct analytical planes without visual disruption.

### Semantic & Accents
- **Primary Accent (Gaze)** (`#F0A500`): Amber-gold. Reserved for high-value targets, confirmed verdicts, critical calls to action, active navigation pins, and central intelligence nodes. It is used sparingly to preserve immediate optical detection.
- **Signal / Confidence (Electric Indigo)** (`#6B4FFF`): Link analysis edges, entity correlation confidence levels, telemetry metrics, and non-critical active indicators.
- **Threat / Alert (Deep Crimson)** (`#C92A2A`): High-risk indicators, flagged UPI IDs, active money mule clusters, and critical alert notices.
- **Confirmed / Safe (Forest Green)** (`#2A9D4E`): Cleared accounts, verified identity chains, and authenticated integrity checks.

### Typography Levels
- **Primary Text**: `#E8E6F2` (clean, high-contrast readability against dark substrates).
- **Secondary Text**: `#8884A8` (metadata, structural labels, table column headers).
- **Muted Text**: `#4A4768` (disabled states, inactive stamps, structural watermarks).

## Typography

The type system is strictly partitioned into **Command & Structuring** (`Space Grotesk`) and **Technical & Intelligence Data** (`JetBrains Mono`). Standard corporate fonts like Inter or Roboto are explicitly prohibited.

### Execution Rules
- **Space Grotesk**: Applied to dossier titles, panel labels, case headers, and action commands. The slightly technical, geometric posture imparts institutional authority without appearing decorative.
- **JetBrains Mono**: Applied without exception to cryptographically sensitive strings, IP addresses, transaction hashes, IFSC codes, bank account sequences, CDR timestamps, and tabular data values.
- **Case Formatting**: All section labels, operational tags, and metric subtitles are set in uppercase (`text-transform: uppercase`) with a track-out of `+0.08em` using `label-xs` or `data-sm`.
- Numbers within tables and metrics must always utilize tabular figures (`font-variant-numeric: tabular-nums`).

## Layout & Spacing

Layout geometry follows an uncompromising 8px baseline rhythm tailored for multi-screen investigation stations. Content is perpetually **left-aligned** to sustain direct eye tracking across wide dashboards; it is never centered.

### Structural Framework
- **Left Navigation Rail**: Fixed width of exactly `56px`. Houses monochrome iconography stacked along the vertical axis with a `4px` amber selection bar flush to the left edge on active tools.
- **Main Canvas**: Fluid grid anchored to the edge of the navigation rail. 
- **Grid Architecture**: 12-column dynamic grid with `16px` gutters (`gutter`) and `24px` outer canvas margins (`margin`). For forensic workspaces exceeding 1920px width, layout sections stretch to accommodate continuous event logs and node graphs rather than clamping into a boxed container.
- **Component Padding Scale**:
  - `space-xs` (4px): Dense element gaps, inner badge margins, micro-status tags.
  - `space-sm` (8px): Icon-to-label gaps, input field vertical padding, condensed list item spacing.
  - `space-md` (16px): Card internal padding, structural grid gaps between metric tiles.
  - `space-lg` (24px): Inter-panel structural margins, header-to-content separators.
  - `space-xl` (32px): Dossier section demarcations, major analysis module separators.

## Elevation & Depth

Spatial layering does not rely on soft blurs or drop shadows. Depth is communicated strictly through **Tonal Shifting** and **Mist Outlines**.

### Elevation Stack
1. **Floor (Level 0)**: Background `#0D0B14`. Base operational layer, graph network canvases, and workspace viewports.
2. **Structural Planes (Level 1)**: Surface `#13111E`. Left rail, top command bar, intelligence feed wrappers, and primary dashboard quadrants. Bound by a solid `1px` border of `#2A2640`.
3. **Contained Units (Level 2)**: Card Surface `#1C1929`. Entity record panels, forensic metric cards, data grids, and filter toolbars. Edge-defined with `1px` `#2A2640`.
4. **Interactive Overlays (Level 3)**: Popovers, context menus, case quick-views, and transaction inspection drawers. Layered with `#1C1929` and reinforced with a dual border: an outer `1px solid #2A2640` and an inner high-contrast `1px solid #3A355A` to delineate crisp edge boundary against the dark background.

Drop shadows are excluded entirely, with one functional exception: active critical target nodes on investigation graphs utilize an ambient gold perimeter halo (`0 0 12px rgba(240, 165, 0, 0.25)`) to direct urgent investigative priority.

## Shapes

The design language uses razor-sharp, disciplined architectural geometry. 

- **Global Radius**: A uniform `4px` corner radius (`roundedness: 1`) is applied systematically across all interactive controls, input containers, panels, data cells, and nested cards. 
- **Strict Anti-Pill Stance**: Buttons, search inputs, and container panels must never use rounded or pill geometries. They remain strict 4px clipped rectangles.
- **Pill Shape Exception**: Status badges and state chips are the sole elements permitted to utilize full rounded caps (`border-radius: 9999px`). This immediate geometric divergence immediately signals non-interactive state metadata versus actionable operational triggers.

## Components

### Buttons
- **Primary (Execution)**: Solid `#F0A500` background, `#0D0B14` bold text (`Space Grotesk`, weight 600). Strictly rectangular with a uniform `4px` radius. Hover state shifts to `#FFB81C`; active state triggers a 1px inner inset ring.
- **Secondary (Analytical)**: `#1C1929` background, `1px solid #2A2640` border, `#E8E6F2` text. Hover shifts border color to `#6B4FFF` and background to `#242036`.
- **Destructive / Override**: `#1C1929` background with `1px solid #C92A2A` border and `#C92A2A` text. Hover shifts to solid `#C92A2A` with `#FFFFFF` text.

### Badges & Status Chips
- **Geometry**: The only elements built with full pill caps (`rounded-full`). Compact height of `20px` or `24px` with horizontal padding of `8px`.
- **Threat (Red)**: Background `rgba(201, 42, 42, 0.16)`, border `1px solid rgba(201, 42, 42, 0.4)`, text `#FF6B6B`.
- **Verified / Clean (Green)**: Background `rgba(42, 157, 78, 0.16)`, border `1px solid rgba(42, 157, 78, 0.4)`, text `#51CF66`.
- **Intelligence Signal (Indigo)**: Background `rgba(107, 79, 255, 0.16)`, border `1px solid rgba(107, 79, 255, 0.4)`, text `#A594FF`.
- **High-Value Target (Amber)**: Background `rgba(240, 165, 0, 0.16)`, border `1px solid rgba(240, 165, 0, 0.4)`, text `#F0A500`.

### Data Grids & Lists
- **Rows**: Surface `#13111E` alternating or separated by a crisp `1px solid #2A2640` horizontal baseline divider. Hover state applies an immediate background change to `#1C1929`.
- **Headers**: Sticky, rendered in `label-xs` (`Space Grotesk`, 10px, uppercase, tracking `+0.08em`) with `#8884A8` text.
- **Values**: Rendered in `JetBrains Mono` (`data-md` or `data-sm`) to support strict vertical character alignment across hashes, timestamps, and rupee amounts.

### Form Inputs & Search Fields
- **Container**: Background `#1C1929`, border `1px solid #2A2640`, radius `4px`.
- **Focus**: Border switches cleanly to `#F0A500` (no outer blur rings).
- **Text**: `#E8E6F2` primary text, placeholder text in `#4A4768`.

### Specialized Domain Components
- **Hash & Wallet Block**: Dedicated inline container styled in `#13111E` with a `1px solid #2A2640` frame. JetBrains Mono font with an integrated micro-action button to copy or append directly to the current subpoena bundle.
- **Node Graph Link Indicator**: Entity relationships within link analysis display confidence percentage badges directly overlaid on connective vector lines, color-coded by the Signal palette (`#6B4FFF`).
- **Chain of Custody Timestamp Stamp**: Fixed structural tag set in `data-sm` with a left amber indicator mark (`2px solid #F0A500`), logging UTC and IST forensic verification markers.