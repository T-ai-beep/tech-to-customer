

import React from "react";

type SidebarItemProps = {
  title: string;
  icon?: React.ComponentType<{ className?: string }>;
};

export default function Sidebar({ items }: { items: SidebarItemProps[] }) {
  return (
    <aside
      role="navigation"
      aria-label="Admin sidebar"
      className="z-20 max-w-70 fixed left-2 shadow-md bottom-2 top-18 bg-gradient-to-r from-primary from-50% to-primary/50 w-1/4 from backdrop-blur-sm content-start [--padding:calc(var(--spacing)*2)] [--radius:calc(var(--spacing)*4)] rounded-sm py-2 px-1.5 grid"
    >
      {items.map((item) => (
        <SidebarItem key={item.title} title={item.title} icon={item.icon} />
      ))}
    </aside>
  );
}


function SidebarItem({ title, icon: Icon }: SidebarItemProps) {
  return (
    <div className="h-8 grid grid-cols-[16px_1fr] py-2 px-1.5 items-center rounded-[calc(var(--radius)-var(--padding))] gap-2 hover:bg-secondary/50 cursor-pointer transition-colors">
      {Icon ? (
        <Icon className="w-4 h-4" />
      ) : (
        <span className="block h-full w-full" aria-hidden />
      )}
      <span className="text-sm h-full flex flex-row items-center">{title}</span>
    </div>
  );
}
