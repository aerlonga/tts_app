import { Clapperboard, Film, Home, Search, Settings2, Sparkles, Volume2 } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/scripts', label: 'Script Studio', icon: Sparkles },
  { to: '/tts', label: 'TTS Studio', icon: Volume2 },
  { to: '/broll', label: 'B-Roll Search', icon: Search },
  { to: '/assembly', label: 'Video Assembly', icon: Clapperboard },
  { to: '/shorts', label: 'Shorts Generator', icon: Film },
  { to: '/settings', label: 'Settings', icon: Settings2 },
];

export function Sidebar() {
  return (
    <aside className="sticky top-0 hidden h-screen w-[280px] shrink-0 border-r border-[var(--border)] bg-[linear-gradient(180deg,rgba(8,10,12,0.98),rgba(14,16,20,0.96))] px-6 py-8 lg:block">
      <div className="rounded-[28px] border border-[var(--border2)] bg-[radial-gradient(circle_at_top,rgba(200,132,10,0.18),transparent_55%),var(--bg2)] p-6">
        <p className="text-xs uppercase tracking-[0.4em] text-[var(--amber)]">TTS App</p>
        <h1 className="mt-3 font-display text-5xl uppercase leading-none tracking-[0.08em] text-[var(--text)]">
          Dark
          <br />
          Pipeline
        </h1>
        <p className="mt-4 text-sm text-[var(--text2)]">
          Frontend React consumindo apenas a API FastAPI. Script, TTS, busca de assets e montagem em um fluxo contínuo.
        </p>
      </div>

      <nav className="mt-8 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm transition',
                isActive
                  ? 'border-[var(--amber)] bg-[var(--amber)]/10 text-[var(--amber)]'
                  : 'border-transparent text-[var(--text2)] hover:border-[var(--border2)] hover:bg-[var(--bg2)] hover:text-[var(--text)]',
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
