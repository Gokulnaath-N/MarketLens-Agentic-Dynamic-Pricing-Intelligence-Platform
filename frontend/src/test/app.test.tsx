import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { formatCurrency, formatPercent, formatNumber } from '@/lib/formatters'
import { API_BASE_URL } from '@/lib/api-client'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { DraggableWidgetGrid } from '@/components/ui/draggable-widget-grid'

describe('Formatters & Utilities', () => {
  it('formats currency correctly with GBP symbol', () => {
    expect(formatCurrency(12.75, 'GBP')).toBe('£12.75')
    expect(formatCurrency(500, 'USD')).toBe('$500.00')
    expect(formatCurrency(null)).toBe('N/A')
  })

  it('formats percentages correctly', () => {
    expect(formatPercent(0.124, 1)).toBe('12.4%')
    expect(formatPercent(0.3125, 2)).toBe('31.25%')
    expect(formatPercent(undefined)).toBe('N/A')
  })

  it('formats numbers with thousands separators', () => {
    expect(formatNumber(1067371)).toBe('1,067,371')
    expect(formatNumber(null)).toBe('N/A')
  })

  it('verifies default API base URL is configured', () => {
    expect(API_BASE_URL).toContain('http')
  })
})

describe('Core Component Rendering', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  it('renders NotFoundPage with back to overview link', () => {
    render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>
    )

    expect(screen.getByText(/404 - Page Not Found/i)).toBeDefined()
    expect(screen.getByText(/Back to Overview/i)).toBeDefined()
  })

  it('renders DraggableWidgetGrid component with items', () => {
    const items = [
      { id: 'w1', size: 'sm' as const, label: 'Widget 1' },
      { id: 'w2', size: 'sm' as const, label: 'Widget 2' },
    ]

    render(
      <DraggableWidgetGrid
        items={items}
        renderItem={(item) => <div data-testid={`content-${item.id}`}>Content</div>}
      />
    )

    expect(screen.getByRole('list')).toBeDefined()
  })
})
