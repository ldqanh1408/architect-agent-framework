# Web Application / Frontend Bounded Context (`01_frontend_architecture`)

When the system includes one or more web applications or SPAs (e.g., workspace SPA and telemetry/observer console), decompose each application into its own bounded context under `architecture/02-domains/01_frontend_architecture/<NN-app-slug>/<skill>/` with dedicated concern folders:

- `00-overview/`: application boundary, actors, runtime modes, and module topology.
- `11-ui-surface/`: route map, view states, component catalog, definition forms/actions, and user journeys.
- `12-state/`: client state store, persistence, optimistic UI, and realtime/CRDT state synchronization.
- `13-api-consumption/`: REST/RPC service contracts, multiplexed stream bindings, error/timeout recovery, and backend seams (`BE-*`).
- `20-accessibility/`: WCAG compliance, keyboard navigation, focus management, and responsive layout breakpoints.
- `21-performance/`: frame/render latency budgets, bundle splitting, and memory caps.
