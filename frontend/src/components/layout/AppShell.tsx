import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface AppShellProps {
  authenticated: boolean;
}

export function AppShell({ authenticated }: AppShellProps) {
  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <div className="mx-auto flex max-w-[1680px]">
        <Sidebar />
        <main className="min-h-screen flex-1 px-4 py-4 md:px-6 lg:px-8">
          <Header authenticated={authenticated} />
          <Outlet />
        </main>
      </div>
    </div>
  );
}
