import { User } from "firebase/auth";
import GeminiInsights from "./GeminiInsights";
import SystemHealth from "./SystemHealth";

// Note: The user prop is currently unused, but may be needed for GeminiInsights props later.
// Consider if user.uid should be passed to GeminiInsights.
interface DashboardProps {
  user: User;
}

export default function Dashboard({ user }: DashboardProps) {
  return (
    <div className="dashboard-tab">
      <h2 class="text-2xl font-bold tracking-tight text-white mb-6">Dashboard</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SystemHealth />
        {/* Assuming GeminiInsights needs a userId prop. The `user` object from AuthGate will need to be passed down. */}
        <GeminiInsights userId={user.uid} />
      </div>
    </div>
  );
}
