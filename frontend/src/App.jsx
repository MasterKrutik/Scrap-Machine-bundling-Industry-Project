import { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import AdminDashboard from "./pages/AdminDashboard";
import UserDashboard from "./pages/UserDashboard";
import Sidebar from "./components/Sidebar";
import "./App.css";

function AppContent() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");
  const [alertCount, setAlertCount] = useState(0);

  if (!user) return <LoginPage />;

  const Dashboard = user.role === "Admin" ? AdminDashboard : UserDashboard;

  return (
    <div className="app-layout">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        alertCount={alertCount}
      />
      <main className="main-content">
        <Dashboard
          activeTab={activeTab}
          alertCount={alertCount}
          setAlertCount={setAlertCount}
        />
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
