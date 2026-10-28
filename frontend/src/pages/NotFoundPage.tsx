import React from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, ArrowLeft, Home } from 'lucide-react'

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-6 space-y-4">
      <div className="size-16 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
        <AlertCircle className="size-8" />
      </div>

      <h1 className="text-3xl font-bold text-white tracking-tight">404 - Page Not Found</h1>
      <p className="text-sm text-zinc-400 max-w-md">
        The requested analytics view does not exist in MarketLens AI. Please return to the overview dashboard.
      </p>

      <div className="pt-2">
        <Link
          to="/"
          className="inline-flex items-center gap-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 text-xs font-semibold shadow-lg shadow-brand-500/20 transition-all"
        >
          <Home className="size-4" />
          Back to Overview
        </Link>
      </div>
    </div>
  )
}
