# NER-LogiAI

NER-LogiAI is a polished Phase 1 frontend for a Northeast India Regional Logistics Intelligence Platform. It demonstrates a route-input → unified analysis API → risk assessment → route recommendation flow without overstating prototype data as live intelligence.

## What is included

- Landing page with original NER-LogiAI identity
- Demo access login screen (no real authentication implemented)
- Responsive intelligence dashboard
- Functional route-analysis form with loading, success, validation, and fallback states
- Illustrative corridor map overlay, clearly labeled as demo geometry
- Interactive Leaflet/OpenStreetMap route map with Northeast India focus, origin/destination markers, available route alternatives, backend-selected route highlighting, auto-fit, and attribution
- Risk gauge, component breakdown, prototype weights, and calculation explainer
- Accessible route comparison table with selectable recommendations
- Alerts and disruptions view with `DEMO ALERT` labeling
- Model transparency page with a visual processing pipeline and limitations
- Centralized API service with `VITE_API_BASE_URL` configuration

## Local development

```bash
pnpm install
pnpm dev
```

The app runs on Vite and uses the existing static WebDev scaffold.

## API integration

When Demo Mode is disabled, the frontend calls `POST http://127.0.0.1:8000/api/routes/calculate` with origin/destination coordinates and `alternative_count: 2`. Configure the services with `VITE_API_BASE_URL` and `VITE_ROUTE_GENERATION_URL`:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 VITE_ROUTE_GENERATION_URL=http://127.0.0.1:8000/api/routes/calculate pnpm dev
```

The UI intentionally stays in Demo Mode by default. Demo values match the requested API response shape and are clearly labeled. In API mode, fewer than three alternatives may be returned; the UI displays only the routes provided and never fabricates additional geometry. No real-time incident or traffic claims are made.

## Design direction

The interface uses a control-room editorial system: deep navy navigation, ice-blue work surfaces, cyan accents, restrained glows, Manrope for product typography, and DM Mono for telemetry labels and metrics.
