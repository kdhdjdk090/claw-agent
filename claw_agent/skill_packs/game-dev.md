# Game Development Skill Pack

## Game Design Fundamentals
- **Core Loop**: What does the player do every 30 seconds? (Act → Reward → Progress → Act)
- **Second Loop**: What drives engagement over hours? (Build → Challenge → Unlock → Build)
- **Meta Loop**: What keeps players over weeks/months? (Season → Rank → Collection → Social)
- **Game Feel**: Input responsiveness (< 100ms), animation anticipation, screen shake, particles
- **Balance**: Dominant strategies = broken design. Every choice should have meaningful tradeoffs

## Engine Patterns
- **Entity Component System**: Entities are IDs. Components are data. Systems are behavior
- **Scene/Level Management**: Additive loading for shared UI. Async loading with progress
- **Object Pooling**: Pre-allocate frequently spawned objects (bullets, particles, enemies)
- **State Machines**: Hierarchical FSM for character states (Idle → Run → Jump → Fall)
- **Event Bus**: Decouple systems via events. Score system doesn't know about UI — it fires events

## Performance
- **60 FPS Budget**: 16.67ms per frame. Profile before optimizing
- **Draw Calls**: Batch materials, atlas textures, instanced rendering
- **Physics**: Fixed timestep. Reduce collision layers. Simple shapes over mesh colliders
- **Memory**: Pool objects. Stream large assets. Compress textures (ASTC mobile, BC7 desktop)
- **LOD**: Level of detail for meshes, shadows, particle counts based on camera distance

## Multiplayer
- **Authority Model**: Server-authoritative for competitive. Client-predicive with reconciliation
- **Lag Compensation**: Input buffering, extrapolation, interpolation between server snapshots
- **Replication**: Only replicate what changed. Delta compression. Relevancy filtering
- **Lobbies/Matchmaking**: Elo/MMR-based. Connection quality as a factor

## Audio
- **Layered Music**: Stems that add/remove based on gameplay intensity
- **Spatial Audio**: 3D positioning, occlusion, reverb zones
- **Sound Design**: Anticipation → Impact → Decay. Layer multiple sounds for richness
- **Mix Priorities**: Gameplay clarity > atmosphere > music. Ducking for important sounds

## QA & Testing
- **Smoke Test**: Core loop works. Can start game, play, save, load, quit
- **Regression Suite**: Automated tests for critical paths after every build
- **Playtest Protocol**: Structured observation + exit survey. What frustrated them?
- **Performance Profile**: Frame time, draw calls, memory, load times on target hardware
