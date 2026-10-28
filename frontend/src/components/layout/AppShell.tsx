import React, { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

export const AppShell: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex flex-col md:flex-row relative overflow-x-hidden selection:bg-brand-500/30 selection:text-brand-300">
      {/* Background Cosmic Atmosphere */}
      <div className="glow-orb top-[-100px] left-[-100px] size-[500px] bg-brand-600/10 pointer-events-none" />
      <div className="glow-orb top-[40%] right-[-100px] size-[600px] bg-indigo-600/10 pointer-events-none" />
      <div className="glow-orb bottom-[-100px] left-[30%] size-[500px] bg-emerald-600/5 pointer-events-none" />

      {/* Desktop Sidebar */}
      <div className="hidden md:block">
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed(!collapsed)}
        />
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative z-10 w-72 h-full bg-[#0d0d12]">
            <Sidebar
              collapsed={false}
              onToggle={() => setMobileMenuOpen(false)}
              onNavigateMobile={() => setMobileMenuOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 relative z-10">
        <Topbar onOpenMobileMenu={() => setMobileMenuOpen(true)} />
        <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
