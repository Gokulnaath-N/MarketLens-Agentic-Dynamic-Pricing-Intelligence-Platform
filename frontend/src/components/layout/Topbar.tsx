import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { Menu, Activity, ShieldAlert, Cpu } from 'lucide-react'

interface TopbarProps {
  onOpenMobileMenu: () => void
}

export const Topbar: React.FC<TopbarProps> = ({ onOpenMobileMenu }) => {
  // Query backend health
  const { data: health, isError } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 15000,
    retry: 1,
  })

  return (
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-white/10 bg-[#09090b]/80 px-4 md:px-8 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenMobileMenu}
          className="md:hidden flex size-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-zinc-300 hover:text-white"
          aria-label="Open navigation menu"
        >
          <Menu className="size-5" />
        </button>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-brand-500/30 bg-brand-500/10 px-2.5 py-0.5 text-[11px] font-medium text-brand-300">
            <Cpu className="size-3 text-brand-400" />
            Phase 6 Production Dashboard
          </span>
        </div>
      </div>

      {/* Backend API Connection & Status Badges */}
      <div className="flex items-center gap-3">
        {isError ? (
          <div className="flex items-center gap-2 rounded-full border border-rose-500/30 bg-rose-500/10 px-3 py-1 text-xs text-rose-300">
            <ShieldAlert className="size-3.5 text-rose-400 animate-pulse" />
            <span className="hidden sm:inline font-mono">Backend Offline</span>
            <span className="sm:hidden font-mono">Offline</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
            <span className="relative flex size-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
            </span>
            <span className="font-mono text-[11px]">
              {health?.status === 'healthy' ? 'FastAPI Connected' : 'Connecting...'}
            </span>
          </div>
        )}

        <div className="hidden lg:flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[11px] text-zinc-400 font-mono">
          <Activity className="size-3 text-zinc-400" />
          <span>v0.1.0-alpha</span>
        </div>
      </div>
    </header>
  )
}
