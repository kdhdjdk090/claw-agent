# Frontend Skill Pack

## React Patterns
- Functional components only. No class components in new code
- Custom hooks extract reusable logic: `useDebounce`, `useLocalStorage`, `useMediaQuery`
- Co-locate: component + styles + tests + types in same directory
- Composition over configuration — render props and children over mega-prop components
- Memoize expensive renders: `React.memo` for pure display, `useMemo`/`useCallback` for stable references

## State Management
- Local state (`useState`) for UI-only state (open/closed, hover, form fields)
- URL state for shareable state (filters, pagination, search params)
- Server state via React Query / SWR / TanStack Query — NOT in Redux
- Global client state (Zustand/Jotai) only for cross-cutting concerns (theme, auth, notifications)

## Next.js Best Practices
- App Router: React Server Components by default, `"use client"` only when needed
- Data fetching in Server Components, not in client useEffect
- Route handlers (`route.ts`) for API endpoints, Server Actions for mutations
- Static generation (`generateStaticParams`) for known paths, ISR for dynamic content
- Metadata API for SEO — `generateMetadata()` per page

## Performance
- Code split routes automatically (Next.js does this). Lazy-load heavy components
- Images: `next/image` with proper `width`/`height` or `fill`. WebP/AVIF formats
- Fonts: `next/font` to eliminate FOIT/FOUT
- Bundle analysis: `@next/bundle-analyzer` to find bloat
- Core Web Vitals: LCP < 2.5s, INP < 200ms, CLS < 0.1

## CSS / Styling
- Tailwind CSS for utility-first. Design tokens via `tailwind.config`
- Component libraries: shadcn/ui (copy-paste, full control) over heavyweight UI kits
- CSS Modules or Tailwind — avoid CSS-in-JS in Server Components
- Responsive: mobile-first breakpoints. Touch targets ≥ 44px

## TypeScript
- Strict mode always. No `any` — use `unknown` + type guards
- Zod for runtime validation at API boundaries
- Discriminated unions over optional fields for state variants
- Path aliases: `@/components/*` not `../../../components/*`
