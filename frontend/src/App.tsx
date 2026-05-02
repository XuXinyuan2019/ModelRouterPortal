import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import GuidePage from "./pages/GuidePage";
import DashboardPage from "./pages/DashboardPage";
import ModelMarketPage from "./pages/ModelMarketPage";
import ModelDetailPage from "./pages/ModelDetailPage";
import ApiKeysPage from "./pages/ApiKeysPage";
import BalancePage from "./pages/BalancePage";
import UsagePage from "./pages/UsagePage";
import SettingsPage from "./pages/SettingsPage";
import PlaygroundPage from "./pages/PlaygroundPage";

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<GuidePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected routes */}
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/models" element={<ModelMarketPage />} />
              <Route path="/models/:modelId" element={<ModelDetailPage />} />
              <Route path="/playground" element={<PlaygroundPage />} />
              {/* Placeholder routes for future phases */}
              <Route path="/api-keys" element={<ApiKeysPage />} />
              <Route path="/balance" element={<BalancePage />} />
              <Route path="/usage" element={<UsagePage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>

            {/* Default redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ConfigProvider>
  );
}
