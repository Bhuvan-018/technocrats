import { ReactNode } from 'react';
import { TopBar } from './TopBar';
import { SideMenu } from './SideMenu';
import { BottomBar } from './BottomBar';

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <div className="flex-1 flex overflow-hidden">
        <SideMenu />
        <div className="flex-1 flex flex-col overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto">
            {children}
          </main>
          <BottomBar />
        </div>
      </div>
    </div>
  );
}
