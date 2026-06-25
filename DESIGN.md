---
tokens:
  colors:
    backgrounds:
      - name: bg-primary
        hex: "#070b14"
        description: "Primary background, darkest navy used in hero sections"
      - name: bg-secondary
        hex: "#0b1221"
        description: "Secondary background, slightly lighter navy for contrast"
      - name: bg-tertiary
        hex: "#0b1324"
        description: "Tertiary background, deep navy with blue tint"
      - name: bg-overlay-dark
        hex: "#06101280"
        description: "Dark semi-transparent overlay, 50% opacity navy"
      - name: surface
        hex: "rgba(17, 24, 39, 0.88)"
        description: "Card and panel surface, semi-transparent darker blue"
      - name: surface-strong
        hex: "rgba(24, 34, 56, 0.95)"
        description: "Elevated surface for prominent containers, higher opacity"
      - name: surface-subtle
        hex: "rgba(255, 255, 255, 0.04)"
        description: "Very subtle surface, minimal contrast for input backgrounds"
    
    text:
      - name: text-primary
        hex: "#edf2ff"
        description: "Primary text, light off-white on dark backgrounds"
      - name: text-muted
        hex: "#99a6bd"
        description: "Muted text for secondary information and placeholders"
      - name: text-muted-light
        hex: "#94a3b8"
        description: "Lighter muted text, used in footers and supplementary info"
    
    accents:
      - name: accent-primary
        hex: "#8b95ff"
        description: "Primary accent, soft purple used throughout the UI"
      - name: accent-secondary
        hex: "#58a6ff"
        description: "Secondary accent, bright cyan-blue for gradients and highlights"
      - name: accent-tertiary
        hex: "#a98bff"
        description: "Tertiary accent, lavender purple for gradient endpoints"
      - name: accent-legacy
        hex: "#fd6500"
        description: "Legacy accent, vibrant orange used in older product pages"
      - name: accent-danger
        hex: "#ff6b8b"
        description: "Danger/warning state color, soft red for alerts"
    
    borders:
      - name: border-default
        hex: "rgba(255, 255, 255, 0.09)"
        description: "Default border color, subtle white 9% opacity"
      - name: border-light
        hex: "rgba(255, 255, 255, 0.1)"
        description: "Light border, 10% opacity white"
      - name: border-lighter
        hex: "rgba(255, 255, 255, 0.07)"
        description: "Lighter border, 7% opacity for subtle dividers"
    
    gradients:
      - name: gradient-primary
        stops: ["#8b95ff", "#58a6ff"]
        angle: "135deg"
        description: "Primary gradient from purple to cyan-blue, primary button and accents"
      - name: gradient-purple-blue
        stops: ["rgba(139, 149, 255, 0.2)", "transparent"]
        description: "Radial gradient purple, background decoration at top-left"
      - name: gradient-cyan-blue
        stops: ["rgba(90, 168, 255, 0.16)", "transparent"]
        description: "Radial gradient cyan, background decoration at top-right"
      - name: gradient-background
        stops: ["#070b14 0%", "#0b1221 45%", "#0b1324 100%"]
        angle: "180deg"
        description: "Primary page background gradient, dark navy to blue"
  
  typography:
    family: "Inter, Segoe UI, system-ui, -apple-system, sans-serif"
    scales:
      - name: heading-1
        size: "2rem"
        size-responsive: "clamp(2rem, 4vw, 3.2rem)"
        weight: 700
        letter-spacing: "-0.02em"
        line-height: 0.95
        description: "Hero title, large responsive heading"
      - name: heading-2
        size: "1.5rem"
        weight: 700
        line-height: 1.2
        description: "Section title, bold and prominent"
      - name: heading-3
        size: "1.25rem"
        weight: 700
        line-height: 1.3
        description: "Subsection title"
      - name: body-large
        size: "1rem"
        weight: 400
        line-height: 1.5
        description: "Large body text, main content"
      - name: body-regular
        size: "0.875rem"
        weight: 400
        line-height: 1.5
        description: "Regular body text, standard content"
      - name: body-small
        size: "0.75rem"
        weight: 400
        line-height: 1.4
        description: "Small body text, secondary information"
      - name: label-large
        size: "0.875rem"
        weight: 600
        line-height: 1.4
        description: "Large label, navigation and headings"
      - name: label-regular
        size: "0.75rem"
        weight: 600
        line-height: 1.4
        description: "Regular label, form labels and captions"
      - name: label-small
        size: "0.625rem"
        weight: 600
        line-height: 1.2
        description: "Small label, tags and badges"
  
  spacing:
    scale:
      - name: spacing-xs
        value: "4px"
        description: "Extra small spacing"
      - name: spacing-sm
        value: "8px"
        description: "Small spacing"
      - name: spacing-md
        value: "12px"
        description: "Medium spacing"
      - name: spacing-lg
        value: "16px"
        description: "Large spacing"
      - name: spacing-xl
        value: "20px"
        description: "Extra large spacing"
      - name: spacing-2xl
        value: "24px"
        description: "2x extra large spacing"
      - name: spacing-3xl
        value: "28px"
        description: "3x extra large spacing"
      - name: spacing-4xl
        value: "32px"
        description: "4x extra large spacing"
    
    padding:
      - name: padding-compact
        value: "8px 12px"
        description: "Compact padding for buttons and small elements"
      - name: padding-default
        value: "12px 16px"
        description: "Default padding for controls"
      - name: padding-generous
        value: "16px 20px"
        description: "Generous padding for cards and containers"
      - name: padding-large
        value: "20px 24px"
        description: "Large padding for hero sections and cards"
      - name: padding-xl
        value: "26px"
        description: "Extra large padding for hero main content"
    
    margin:
      - name: margin-sm
        value: "4px"
        description: "Small margin between tight elements"
      - name: margin-md
        value: "12px"
        description: "Medium margin between grouped elements"
      - name: margin-lg
        value: "16px"
        description: "Large margin between sections"
      - name: margin-xl
        value: "20px"
        description: "Extra large margin between major sections"
  
  border-radius:
    - name: radius-sm
      value: "6px"
      description: "Small border radius for buttons and inputs"
    - name: radius-md
      value: "12px"
      description: "Medium border radius for cards"
    - name: radius-lg
      value: "14px"
      description: "Large border radius for prominent cards"
    - name: radius-xl
      value: "18px"
      description: "Extra large border radius for hero sections"
    - name: radius-2xl
      value: "20px"
      description: "2x extra large border radius for large containers"
    - name: radius-3xl
      value: "26px"
      description: "3x extra large border radius for prominent hero"
    - name: radius-full
      value: "999px"
      description: "Fully rounded border for pills and badges"
  
  shadows:
    - name: shadow-sm
      value: "0 4px 12px rgba(0, 0, 0, 0.1)"
      description: "Small shadow for lifted elements"
    - name: shadow-md
      value: "0 10px 25px -5px rgba(124, 58, 237, 0.1)"
      description: "Medium shadow with purple tint, cards and panels"
    - name: shadow-lg
      value: "0 18px 48px rgba(0, 0, 0, 0.25)"
      description: "Large shadow for prominent cards"
    - name: shadow-xl
      value: "0 30px 80px rgba(0, 0, 0, 0.35)"
      description: "Extra large shadow for hero sections and dropdowns"
    - name: shadow-accent
      value: "0 4px 6px -1px rgba(124, 58, 237, 0.3)"
      description: "Accent shadow with purple tint for buttons"
    - name: shadow-accent-lg
      value: "0 20px 35px -10px rgba(124, 58, 237, 0.15)"
      description: "Large accent shadow for elevated states"
  
  motion:
    - name: transition-fast
      duration: "180ms"
      easing: "ease"
      description: "Fast transitions for interactive states"
    - name: transition-normal
      duration: "200ms"
      easing: "ease"
      description: "Normal transitions for UI changes"
    - name: transition-slow
      duration: "300ms"
      easing: "ease"
      description: "Slow transitions for modal or significant changes"
    - name: animation-fade-in
      duration: "300ms"
      description: "Fade in animation for appearing elements"
    - name: animation-slide
      duration: "200ms"
      description: "Slide animation for navigation and cards"

---

## Optimistic — Design System

Optimistic is a modern, trust-first e-commerce marketplace designed for the Zambian market. The design system reflects a sophisticated, data-driven aesthetic inspired by global platforms like Optimistic, with a focus on clarity, accessibility, and delightful interaction patterns.

### Design Philosophy

**Trust Through Clarity.** Every design decision prioritizes transparency and user confidence. The dark theme reduces visual fatigue during extended shopping sessions. Accent colors guide attention to critical actions—purchase, verification, and order tracking. Spacing and hierarchy make information instantly scannable for users across different literacy levels.

**Responsive & Inclusive.** The grid-based spacing system and semantic typography scale ensure clarity from mobile to desktop. CSS variables throughout enable consistent theming without hardcoded values.

**Global + Local.** While inspired by international marketplaces, the design acknowledges Zambian contexts—clear mobile-money payment indicators, straightforward delivery status, and trust badges that matter locally.

### Color System

#### The Dark Palette
The primary background (`#070b14`) is a navy-black that feels premium yet accessible. It's overlaid with subtle radial gradients—purple (`rgba(139, 149, 255, 0.2)`) and cyan (`rgba(90, 168, 255, 0.16)`)—creating depth without gimmickry. These gradients are positioned at top-left and top-right corners, framing content with visual sophistication.

Text on this dark canvas uses two primary colors:
- **Primary text** (`#edf2ff`): An off-white, cool-toned to harmonize with the blue palette
- **Muted text** (`#99a6bd`): A soft blue-grey for secondary information, reducing cognitive load

#### Accent System
Three accent colors create a hierarchy of emphasis:

1. **Purple Primary** (`#8b95ff`): The workhorse accent. It appears in buttons, active navigation states, stat highlights, and gradient endpoints. It feels sophisticated and trustworthy—a color for money and security.

2. **Cyan Secondary** (`#58a6ff`): A bright, energetic cyan for button backgrounds and gradient pairs. It draws attention where the purple might feel passive.

3. **Lavender Tertiary** (`#a98bff`): Used in gradients and decorative elements, adding dimensional depth without overwhelming.

A legacy orange accent (`#fd6500`) persists in older product pages—a warm, action-oriented color for call-to-action buttons.

For states, a soft red (`#ff6b8b`) signals danger or attention without aggression.

#### Borders
Borders use white at 7-10% opacity, creating just enough contrast to define regions without harsh lines. This approach keeps the interface cohesive and premium.

### Typography

**Font Family:** Inter with fallbacks to system fonts ensures consistent rendering across devices. Inter is geometric and modern—every character is clear at any size.

**Hierarchy:**
- Headings (h1–h3) use weights 700–800 with tight line-heights, making them commanding but readable.
- Body text defaults to 400-weight, increasing to 600 for labels and navigation.
- Small text (`0.75rem`) is used sparingly, only for secondary metadata.

**Responsive Scaling:**
Hero headings use CSS `clamp()` to scale smoothly between `2rem` and `3.2rem`, ensuring readability from mobile to ultra-wide displays.

**Kerning:**
Large headings use negative letter-spacing (`-0.02em`) to increase visual impact. Labels use `0.08em` letter-spacing for openness and legibility.

### Spacing & Layout

The spacing system is based on an 8px grid (4px, 8px, 12px, 16px, 20px, 24px, 28px, 32px), enabling flexible, mathematically consistent layouts.

**Component Padding:**
- Buttons: `8px 12px` (compact) to `12px 16px` (default)
- Cards: `20px` on all sides
- Hero sections: `26px` or `32px`

**Grid Layouts:**
Dashboard sidebars use 240px fixed width. Main content follows a 1400px max-width constraint. Product grids use `repeat(auto-fill, minmax(200px, 1fr))` for fluidity.

**Gaps:**
14px gaps separate navbar components. 20px gaps separate dashboard cards. Sidebar items have 4px margins for tight grouping.

### Elevation & Shadows

Shadows are integral to the dark theme, creating layered depth:

- **Small shadows** (`0 4px 12px rgba(0, 0, 0, 0.1)`): Gentle lifts for subtle elevation
- **Medium shadows** (`0 10px 25px -5px rgba(124, 58, 237, 0.1)`): Card elevation with a purple tint
- **Large shadows** (`0 18px 48px rgba(0, 0, 0, 0.25)`): Prominent containers and popovers
- **Extra large shadows** (`0 30px 80px rgba(0, 0, 0, 0.35)`): Hero sections and top-level modals

The purple-tinted shadows (`rgba(124, 58, 237, 0.1)` and `rgba(124, 58, 237, 0.3)`) subtly reinforce brand accent without overwhelming the dark background.

### Border Radius

Radius choices communicate hierarchy:

- **6px** (`radius-sm`): Tight radius for input fields and small buttons
- **12–14px** (`radius-md` to `radius-lg`): Card borders, most UI elements
- **18–20px** (`radius-xl` to `radius-2xl`): Prominent cards and containers
- **26px** (`radius-3xl`): Hero sections, maximum softness
- **999px** (`radius-full`): Pill-shaped buttons and badges

### Motion

All transitions use `ease` easing with three speeds:

- **180ms** (fast): Interactive state changes (hover, focus, toggle)
- **200ms** (normal): Standard UI changes (card slides, nav transitions)
- **300ms** (slow): Modals, offscreen panels, significant reflows

Animations are purposeful—hover states lift buttons 1px, cards lift 4px, creating tactile feedback without distraction.

### Component Patterns

#### Navbar
The sticky navbar uses a semi-transparent dark background (`rgba(6, 10, 18, 0.64)`) with a subtle backdrop blur (18px). It contains:
- Logo on the left (max-width 140px)
- Search bar with category dropdown (flex-grows to fill space)
- Action buttons (login, cart, etc.)

Buttons within the navbar use the primary gradient (`linear-gradient(135deg, #8b95ff, #58a6ff)`).

#### Cards
Cards are the bread-and-butter UI element. Standard card properties:
- `background: rgba(17, 24, 39, 0.88)`
- `border: 1px solid rgba(255, 255, 255, 0.1)`
- `border-radius: 12px`
- `padding: 20px`

On hover, the border brightens to `rgba(139, 149, 255, 0.3)` and shadow increases, signaling interactivity.

#### Buttons
Three button variants:

1. **Primary** (`--accent`): Gradient background, bold weight, used for major actions
2. **Secondary** (`ghost`): Transparent with light border, for tertiary actions
3. **Inline**: Text-only with color shifting on hover

All buttons have 180ms transitions, lifting 1px on hover to signal clickability.

#### Forms
Input fields use a subtle background (`rgba(255, 255, 255, 0.04)`) and a 1px border (`rgba(255, 255, 255, 0.12)`). Labels are uppercase, 12px, 600-weight, with 0.08em tracking. Placeholder text uses the muted color (`#99a6bd`).

#### Dashboard Layout
Dashboards follow an Optimistic-inspired grid:
```
[Sticky Navbar]
[Container]
  [Sidebar | Main Content]
    Cards, Tables, Stats
```

Sidebar: 240px fixed, sticky at 80px scroll. Main: flexible, gap-20 between elements.

#### Stats & Metrics
Metrics use:
- Light accent background: `rgba(139, 149, 255, 0.08)`
- 24px bold value in accent color
- 12px muted label

### Responsive Behavior

At `max-width: 768px`:
- Sidebar collapses/hides
- Top navigation shrinks
- Grids become single-column
- Paddings reduce by 25%

At `max-width: 480px`:
- Full-width single columns
- Reduced nav gap and padding
- Larger touch targets (min 44px height)

### The Aesthetic

Optimistic's design is **calm yet energetic**. The dark navy background feels like evening shopping—comfortable, intimate, focused. The purple-cyan accents inject modern energy without aggression. The generous whitespace (achieved through spacing and subtle borders) prevents information overload.

Users experience:
- **Confidence** from clear information hierarchy and consistent theming
- **Speed** from fast transitions and predictable interactions
- **Trust** from a mature, premium aesthetic that prioritizes their data
- **Delight** from subtle animations and thoughtful hover states

Every color, shadow, and spacing decision serves the core goal: enabling Zambian buyers, sellers, and couriers to exchange goods with confidence in a beautiful, fast, trustworthy marketplace.
