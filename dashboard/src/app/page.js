// app/page.js
import ServerDashboard from '@/components/ServerDashboard';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <ServerDashboard />
    </main>
  );
}