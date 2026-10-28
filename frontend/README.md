# MarketLens AI — Frontend Dashboard

High-end, Webflow-inspired analytics and dynamic pricing dashboard built natively in **React 19 + Vite + TypeScript**.

## Key Features

- **Draggable Widget Grid**: Custom dynamic layout grid (`components/ui/draggable-widget-grid.tsx`) powered by Motion (`motion/react`) with full mouse drag, touch long-press, and keyboard accessibility (Alt + Arrow keys).
- **Fyntic-Inspired Aesthetic**: Deep cosmic dark theme, subtle glowing blue and emerald accents, crisp typography, and responsive card layouts.
- **7 Domain Workspaces**: Overview, Data Explorer, Demand Forecasting, Market Intelligence, Price Optimizer, Experiments, and System Status.
- **Typed API Client**: Single centralized HTTP client using `@tanstack/react-query` with configurable `VITE_API_BASE_URL`.
- **Accessible & Responsive**: Keyboard navigable, contrast verified, and responsive across desktop, tablet, and mobile viewports.

## Tech Stack

- **Framework**: React 19 + TypeScript + Vite 8
- **Styling**: Tailwind CSS + CSS Variables
- **Icons**: Lucide React
- **Animations**: Motion (`motion/react`)
- **Visualizations**: Recharts
- **State & Caching**: TanStack Query (React Query v5)
- **Routing**: React Router v7
- **Testing**: Vitest + React Testing Library + JSDOM

## Available Scripts

In the `frontend` directory:

- `npm run dev`: Start Vite development server at `http://127.0.0.1:5173`.
- `npm run build`: Compile TypeScript and build production bundle into `dist/`.
- `npm run test`: Run automated Vitest unit tests.
- `npm run typecheck`: Run TypeScript compiler type-check (`tsc -b`).
- `npm run preview`: Preview the production build locally.

## Environment Variables

Copy `.env.example` to `.env`:
```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```
*(All variables prefixed with `VITE_` are public to the browser. Do not place private credentials or API keys here.)*
