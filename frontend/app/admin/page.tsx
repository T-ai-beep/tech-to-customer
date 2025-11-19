import Navbar from "@/app/admin/components/Navbar";
import Sidebar from "@/app/admin/components/Sidebar";
import Homepage from "@/app/admin/components/Homepage";
import {
  Home,
  Briefcase,
  Users,
  Building2,
  BarChart3,
  Settings,
} from "lucide-react";

// Page is a server component — client behavior is isolated in child components

export const metadata = {
  title: "Admin View",
};

export default function AdminPage() {
  const items = [
    { type: 'graph', width: '1/2', x: 'users', y: 'time' },
    { type: 'leaderboard', width: '1/4' },
    { type: 'notifications', width: '1/4' },
    { type: 'graph', width: '1/2', x: 'users', y: 'time' },
    { type: 'leaderboard', width: '1/4' },
    { type: 'notifications', width: '1/4' },
  ];
  
  return (
    <div className="bg-background min-h-screen w-full">
      <Navbar />
      <Sidebar
        items={[
          { title: "Home", icon: Home },
          { title: "Jobs", icon: Briefcase },
          { title: "Employees", icon: Users },
          { title: "Branches", icon: Building2 },
          { title: "Analytics", icon: BarChart3 },
          { title: "Settings", icon: Settings },
        ]}
      />
      <Homepage items={items} />
    </div>
  )
}
