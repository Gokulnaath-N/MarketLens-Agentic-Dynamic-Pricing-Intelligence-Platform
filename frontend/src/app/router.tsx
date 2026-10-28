import React from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { OverviewPage } from '@/pages/OverviewPage'
import { DataExplorerPage } from '@/pages/DataExplorerPage'
import { ForecastingPage } from '@/pages/ForecastingPage'
import { MarketIntelligencePage } from '@/pages/MarketIntelligencePage'
import { PriceOptimizerPage } from '@/pages/PriceOptimizerPage'
import { ExperimentsPage } from '@/pages/ExperimentsPage'
import { SystemStatusPage } from '@/pages/SystemStatusPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: 'overview', element: <OverviewPage /> },
      { path: 'data', element: <DataExplorerPage /> },
      { path: 'forecasting', element: <ForecastingPage /> },
      { path: 'market-intelligence', element: <MarketIntelligencePage /> },
      { path: 'pricing', element: <PriceOptimizerPage /> },
      { path: 'experiments', element: <ExperimentsPage /> },
      { path: 'system', element: <SystemStatusPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
