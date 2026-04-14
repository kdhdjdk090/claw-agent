# Mobile Development Skill Pack

## React Native
- Platform-specific files: `Component.ios.tsx` / `Component.android.tsx` when behavior diverges
- Navigation: React Navigation (native stack). Deep linking configured from day one
- State: Zustand/Jotai for client. TanStack Query for server state
- Performance: FlatList over ScrollView for lists. Reanimated for 60fps animations
- Native modules: Turbo Modules for bridging. Only when React Native API is insufficient

## Flutter / Dart
- Widget composition: Small widgets composed into larger ones. No 500-line build methods
- State: BLoC pattern or Riverpod. Provider for simple cases
- Navigation: GoRouter for declarative routing with deep links
- Platform channels: MethodChannel for native API access
- Null safety: Strict. No `!` operator without documented reason

## SwiftUI / iOS
- `@Observable` (iOS 17+) over `ObservableObject`
- View composition: Extract views into separate structs when body exceeds 30 lines
- Navigation: `NavigationStack` with typed `NavigationPath`
- Concurrency: Swift structured concurrency (`async/await`, `TaskGroup`)
- Accessibility: `.accessibilityLabel()`, `.accessibilityHint()` on every interactive element

## Android / Kotlin
- Jetpack Compose: `@Composable` functions. Side effects via `LaunchedEffect`, `rememberCoroutineScope`
- Architecture: MVVM with Repository pattern. ViewModel ↔ Repository ↔ DataSource
- Coroutines: `viewModelScope` for ViewModel work. `Dispatchers.IO` for network/disk
- Room for local DB. Retrofit for network. Hilt for dependency injection
- ProGuard/R8 for release builds. Baseline profiles for startup performance

## Cross-Platform Patterns
- Shared business logic / platform-specific UI when possible
- Offline-first: Local DB + sync queue. Conflict resolution strategy chosen up front
- Push notifications: Firebase Cloud Messaging (Android) + APNs (iOS)
- App lifecycle: Handle background/foreground transitions. Save state before backgrounding
- App Store optimization: Screenshots, keywords, description. A/B test listing elements
