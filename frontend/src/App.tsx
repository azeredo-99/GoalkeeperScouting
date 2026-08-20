import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { Discover } from "./pages/Discover";
import { PlayerProfile } from "./pages/PlayerProfile";
import { Compare } from "./pages/Compare";
import { Similar } from "./pages/Similar";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/discover" replace />} />
        <Route path="/discover" element={<Discover />} />
        <Route path="/player/:player" element={<PlayerProfile />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/similar/:player" element={<Similar />} />
      </Routes>
    </AppShell>
  );
}
