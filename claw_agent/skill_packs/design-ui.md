# Design & UI Skill Pack

## Design System Architecture
- **Token layers**: Primitive → Semantic → Component tokens
  - Primitive: `--color-blue-500`, `--space-4`, `--font-size-16`
  - Semantic: `--color-primary`, `--space-element-gap`, `--font-size-body`
  - Component: `--button-bg`, `--button-padding`, `--card-border-radius`
- **Component categories**: Atoms → Molecules → Organisms → Templates → Pages
- **Documentation**: Every component gets usage guidelines, do/don't examples, accessibility notes

## Visual Design Principles
- **Hierarchy**: Size, weight, color, spacing. One focal point per view
- **Spacing**: Use a consistent scale (4px base: 4, 8, 12, 16, 24, 32, 48, 64)
- **Typography**: Max 2 typefaces. Establish clear type scale with ratios
- **Color**: 60-30-10 rule. Neutral dominant, brand accent, action highlight
- **Contrast**: WCAG AA minimum (4.5:1 for body text, 3:1 for large text)

## Responsive Design
- Mobile-first: Design for smallest screen, enhance for larger
- Breakpoints: 640px (sm), 768px (md), 1024px (lg), 1280px (xl), 1536px (2xl)
- Fluid typography: `clamp(1rem, 2.5vw, 1.5rem)` for smooth scaling
- Touch targets: Minimum 44x44px. 8px minimum spacing between targets
- Container queries for component-level responsiveness

## Accessibility (WCAG 2.2 AA)
- Semantic HTML first: `button`, `nav`, `main`, `article`, `aside`
- ARIA only when HTML semantics are insufficient
- Keyboard navigation: Every interactive element focusable and operable
- Focus management: Visible focus indicator. Logical tab order
- Screen readers: Labels on all inputs, alt text on images, aria-live for dynamic content
- Motion: `prefers-reduced-motion` media query for animations

## Animation & Interaction
- Purpose-driven: Animations guide attention and provide feedback
- Duration: Micro-interactions 100-300ms. Page transitions 300-500ms
- Easing: ease-out for entrances, ease-in for exits, ease-in-out for continuous
- Performance: Use `transform` and `opacity`. Hardware accelerated, no layout triggers
