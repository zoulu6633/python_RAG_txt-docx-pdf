import { ReactNode } from 'react';
import Sidebar from './Sidebar';

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex h-screen bg-[#f8f9fc]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
