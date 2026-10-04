import { useEffect, useRef, useState } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import "./AdminTheme.css";
import {
  searchVillages,
  getDashboardStats,
  getApiRequestTrend,
  getTopStates,
  getStates,
  getDistricts,
  getSubDistricts,
  getVillagesBySubDistrict,
  getApiKeys,
  createAdminApiKey,
  updateAdminApiKey,
  rotateApiKey,
  getAdminUsers,
  updateAdminUser,
  approveAdminUser,
  rejectAdminUser,
  deleteAdminUser,
  getUserStateAccess,
  updateUserStateAccess,
  getAdminLogs,
  getCurrentUser,
  API_BASE_URL,
  type DashboardStats,
  type State,
  type District,
  type SubDistrict,
  type Village as ApiVillage,
  type AdminUserItem,
  type CurrentUser,
  type UserStateAccess,
  type ApiKeyItem,
  type AdminLog,
} from "./api";
type Page =
  | "Dashboard"
  | "Villages"
  | "Users"
  | "API Logs"
  | "Settings";






/* =========================
   NOTIFICATIONS
========================= */

type NotificationType = "success" | "info" | "warning" | "error";

type AppNotification = {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  createdAt: string;
  read: boolean;
};

const NOTIFICATION_STORAGE_KEY = "village_api_notifications";

function readStoredNotifications(): AppNotification[] {
  try {
    const raw = localStorage.getItem(NOTIFICATION_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeStoredNotifications(items: AppNotification[]) {
  try {
    localStorage.setItem(NOTIFICATION_STORAGE_KEY, JSON.stringify(items.slice(0, 50)));
  } catch {
    // Ignore storage errors.
  }
}


/* =========================
   APP
========================= */

function App({ onLogout }: { onLogout?: () => void }) {
  const [page, setPage] = useState<Page>("Dashboard");
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [notifications, setNotifications] = useState<AppNotification[]>(readStoredNotifications);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [toast, setToast] = useState<AppNotification | null>(null);
  const lastLogIdRef = useRef<number | null>(null);

  const pushNotification = (
    title: string,
    message: string,
    type: NotificationType = "info",
    options: { toast?: boolean; persist?: boolean } = {}
  ) => {
    const item: AppNotification = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      title,
      message,
      type,
      createdAt: new Date().toISOString(),
      read: false,
    };

    setNotifications((current) => {
      const next = [item, ...current].slice(0, 50);
      writeStoredNotifications(next);
      return next;
    });

    if (options.toast !== false) {
      setToast(item);
      window.setTimeout(() => {
        setToast((current) => (current?.id === item.id ? null : current));
      }, 4500);
    }
  };

  useEffect(() => {
    let mounted = true;

    const loadCurrentUser = async () => {
      try {
        const user = await getCurrentUser();
        if (mounted) setCurrentUser(user);
      } catch (error) {
        console.error("Unable to load current administrator:", error);
      }
    };

    loadCurrentUser();
    return () => { mounted = false; };
  }, []);

  // Poll backend logs so important live API/security events can appear in the
  // notification center without requiring a WebSocket service.
  useEffect(() => {
    let mounted = true;

    const pollSecurityEvents = async () => {
      try {
        const response = await getAdminLogs({ page: 1, page_size: 20 });
        const logs = response.items || [];
        if (!logs.length || !mounted) return;

        const newestId = Math.max(...logs.map((log) => Number(log.id)));

        if (lastLogIdRef.current === null) {
          lastLogIdRef.current = newestId;
          return;
        }

        const newSecurityLogs = logs.filter((log) => {
          const id = Number(log.id);
          return id > (lastLogIdRef.current || 0) && [401, 403, 429, 500].includes(Number(log.status_code));
        });

        lastLogIdRef.current = Math.max(lastLogIdRef.current, newestId);

        for (const log of newSecurityLogs.reverse()) {
          const status = Number(log.status_code);
          const type: NotificationType = status === 429 ? "warning" : "error";
          pushNotification(
            status === 429 ? "API rate limit alert" : "API security alert",
            `${status} response on ${log.path || "API endpoint"}.`,
            type
          );
        }
      } catch {
        // Do not interrupt the dashboard if notification polling fails.
      }
    };

    pollSecurityEvents();
    const timer = window.setInterval(pollSecurityEvents, 5000);
    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, []);

  const unreadCount = notifications.filter((item) => !item.read).length;

  const handleNotificationClick = () => {
    setShowNotifications((open) => !open);
    setShowProfile(false);
  };

  const handleProfileClick = () => {
    setShowProfile((open) => !open);
    setShowNotifications(false);
  };

  const markNotificationsRead = () => {
    setNotifications((current) => {
      const next = current.map((item) => ({ ...item, read: true }));
      writeStoredNotifications(next);
      return next;
    });
  };

  const markNotificationRead = (id: string) => {
    setNotifications((current) => {
      const next = current.map((item) => item.id === id ? { ...item, read: true } : item);
      writeStoredNotifications(next);
      return next;
    });
  };

  const handleLogout = () => {
    setShowProfile(false);
    setShowNotifications(false);
    onLogout?.();
  };


  return (
    <div className="min-h-screen bg-slate-100 flex">

      <aside className="w-64 bg-slate-950 text-white min-h-screen fixed left-0 top-0">

        <div className="p-6 border-b border-slate-800">

          <h1 className="text-2xl font-bold">
            Village API
          </h1>

          <p className="text-slate-400 text-sm mt-1">
            Admin Platform
          </p>

        </div>


        <nav className="p-4 space-y-2">

          <SidebarButton
            name="Dashboard"
            current={page}
            setPage={setPage}
            icon="▦"
          />

          <SidebarButton
            name="Villages"
            current={page}
            setPage={setPage}
            icon="⌂"
          />

          <SidebarButton
            name="Users"
            current={page}
            setPage={setPage}
            icon="◉"
          />

          <SidebarButton
            name="API Logs"
            current={page}
            setPage={setPage}
            icon="▤"
          />

          <SidebarButton
            name="Settings"
            current={page}
            setPage={setPage}
            icon="⚙"
          />

        </nav>


        <div className="absolute bottom-0 left-0 right-0 p-5 border-t border-slate-800">

          <p className="text-xs text-slate-500">
            Logged in as
          </p>

          <p className="text-sm font-medium mt-1">
            {currentUser?.full_name || "Administrator"}
          </p>
          <p className="text-xs text-slate-400 mt-1 truncate" title={currentUser?.email || ""}>
            {currentUser?.email || "Loading account…"}
          </p>

        </div>

      </aside>


      <main className="ml-64 flex-1 min-h-screen">

        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-10">

          <p className="text-sm text-slate-500">
            Admin Panel
          </p>


          <div className="flex items-center gap-4">

            {/* Notifications */}
            <div className="relative">
              <button
                type="button"
                onClick={handleNotificationClick}
                aria-label="Open notifications"
                aria-expanded={showNotifications}
                className="relative text-xl w-10 h-10 rounded-lg hover:bg-slate-100 transition flex items-center justify-center"
              >
                🔔
                {unreadCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[9px] rounded-full min-w-[18px] h-[18px] px-1 flex items-center justify-center">
                    {unreadCount > 99 ? "99+" : unreadCount}
                  </span>
                )}
              </button>

              {showNotifications && (
                <div className="absolute right-0 top-12 w-96 max-w-[calc(100vw-2rem)] bg-white border border-slate-200 rounded-xl shadow-xl z-50 overflow-hidden">
                  <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-slate-900">Notifications</h3>
                      <p className="text-xs text-slate-500 mt-0.5">Live admin and system alerts</p>
                    </div>
                    {unreadCount > 0 && (
                      <button type="button" onClick={markNotificationsRead} className="text-xs text-blue-600 font-medium hover:underline">
                        Mark all read
                      </button>
                    )}
                  </div>

                  <div className="max-h-[420px] overflow-y-auto divide-y divide-slate-100">
                    {notifications.length === 0 ? (
                      <div className="px-5 py-10 text-center">
                        <div className="text-2xl mb-2">✓</div>
                        <p className="text-sm font-medium text-slate-700">You're all caught up</p>
                        <p className="text-xs text-slate-500 mt-1">Important admin actions and API alerts will appear here.</p>
                      </div>
                    ) : (
                      notifications.map((item) => (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() => markNotificationRead(item.id)}
                          className={`w-full text-left px-4 py-3 hover:bg-slate-50 transition ${!item.read ? "bg-blue-50/50" : ""}`}
                        >
                          <div className="flex gap-3">
                            <span className={`mt-1 w-2.5 h-2.5 rounded-full shrink-0 ${item.type === "success" ? "bg-green-500" : item.type === "warning" ? "bg-amber-500" : item.type === "error" ? "bg-red-500" : "bg-blue-500"}`} />
                            <div className="min-w-0 flex-1">
                              <div className="flex items-start justify-between gap-2">
                                <p className="text-sm font-medium text-slate-800">{item.title}</p>
                                {!item.read && <span className="text-[10px] text-blue-600 font-semibold">NEW</span>}
                              </div>
                              <p className="text-xs text-slate-500 mt-1">{item.message}</p>
                              <p className="text-[10px] text-slate-400 mt-2">{new Date(item.createdAt).toLocaleString()}</p>
                            </div>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Administrator profile */}
            <div className="relative">
              <button
                type="button"
                onClick={handleProfileClick}
                aria-label="Open administrator profile"
                aria-expanded={showProfile}
                className="flex items-center gap-3 rounded-lg px-2 py-1.5 hover:bg-slate-50 transition"
              >
                <div className="w-9 h-9 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
                  {(currentUser?.full_name || currentUser?.email || "A").charAt(0).toUpperCase()}
                </div>

                <div className="text-left">
                  <p className="text-sm font-semibold">{currentUser?.full_name || "Administrator"}</p>
                  <p className="text-xs text-slate-500 max-w-[220px] truncate">{currentUser?.email || "Loading account…"}</p>
                </div>
              </button>

              {showProfile && (
                <div className="absolute right-0 top-14 w-72 bg-white border border-slate-200 rounded-xl shadow-xl z-50 overflow-hidden">
                  <div className="px-4 py-4 border-b border-slate-200">
                    <p className="font-semibold text-slate-900">{currentUser?.full_name || "Administrator"}</p>
                    <p className="text-sm text-slate-600 mt-1 break-all">{currentUser?.email || "Loading account…"}</p>
                    {currentUser?.business_name && <p className="text-xs text-slate-500 mt-1">{currentUser.business_name}</p>}
                    <div className="mt-3 inline-flex items-center gap-2 text-xs text-green-700 bg-green-50 px-2.5 py-1.5 rounded-full">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                      Active session
                    </div>
                  </div>

                  <div className="p-2">
                    <button type="button" onClick={() => { setPage("Settings"); setShowProfile(false); }} className="w-full text-left px-3 py-2.5 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition">
                      ⚙ Settings
                    </button>
                    <button type="button" onClick={handleLogout} className="w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition">
                      ↪ Logout
                    </button>
                  </div>
                </div>
              )}
            </div>

          </div>

        </header>


        <div className="p-8">

          {page === "Dashboard" && (
            <Dashboard />
          )}

          {page === "Villages" && (
            <VillagesPage />
          )}

          {page === "Users" && (
            <UsersPage onNotify={pushNotification} />
          )}

          {page === "API Logs" && (
            <ApiLogsPage />
          )}

          {page === "Settings" && (
            <SettingsPage onNotify={pushNotification} />
          )}

        </div>

        {toast && (
          <div className="fixed right-6 bottom-6 z-[100] w-[360px] max-w-[calc(100vw-3rem)]">
            <div className={`rounded-xl border shadow-2xl px-4 py-3 bg-white ${toast.type === "success" ? "border-green-200" : toast.type === "warning" ? "border-amber-200" : toast.type === "error" ? "border-red-200" : "border-blue-200"}`}>
              <div className="flex items-start gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${toast.type === "success" ? "bg-green-100 text-green-700" : toast.type === "warning" ? "bg-amber-100 text-amber-700" : toast.type === "error" ? "bg-red-100 text-red-700" : "bg-blue-100 text-blue-700"}`}>
                  {toast.type === "success" ? "✓" : toast.type === "error" ? "!" : toast.type === "warning" ? "⚠" : "i"}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-slate-900">{toast.title}</p>
                  <p className="text-xs text-slate-500 mt-1">{toast.message}</p>
                </div>
                <button type="button" onClick={() => setToast(null)} className="text-slate-400 hover:text-slate-700">×</button>
              </div>
            </div>
          </div>
        )}

      </main>

    </div>
  );
}





/* =========================
   SIDEBAR
========================= */

function SidebarButton({
  name,
  current,
  setPage,
  icon,
}: {
  name: Page;
  current: Page;
  setPage: (page: Page) => void;
  icon: string;
}) {

  const active =
    current === name;


  return (
    <button
      onClick={() => setPage(name)}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition ${
        active
          ? "bg-blue-600 text-white"
          : "text-slate-300 hover:bg-slate-800"
      }`}
    >

      <span>
        {icon}
      </span>

      <span>
        {name}
      </span>

    </button>
  );
}


/* =========================
   DASHBOARD
========================= */

function Dashboard() {
  const [dashboardData, setDashboardData] =
    useState<DashboardStats | null>(null);

  const [apiRequestsData, setApiRequestsData] =
    useState<{ day: string; requests: number }[]>([]);

  const [villagesByStateData, setVillagesByStateData] =
    useState<{ state: string; villages: number }[]>([]);

  const [loadingStats, setLoadingStats] =
    useState(false);

  const [statsError, setStatsError] =
    useState("");

  const loadDashboard = async () => {
    try {
      setLoadingStats(true);
      setStatsError("");

      const [stats, requestTrend, topStates] =
        await Promise.all([
          getDashboardStats(),
          getApiRequestTrend(),
          getTopStates(),
        ]);

      setDashboardData(stats);

      setApiRequestsData(
        requestTrend.map((item) => ({
          day: item.day,
          requests: Number(item.requests),
        }))
      );

      setVillagesByStateData(
        topStates.map((item) => ({
          state: item.state_name,
          villages: Number(item.village_count),
        }))
      );
    } catch (error) {
      console.error("Dashboard loading error:", error);
      setStatsError(
        "Unable to load dashboard data from backend."
      );
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-900">
          Dashboard
        </h2>
        <p className="text-slate-500 mt-1">
          Overview of your Village API platform
        </p>
      </div>

      {loadingStats && (
        <div className="mb-5 text-sm text-blue-600">
          Loading dashboard statistics...
        </div>
      )}

      {statsError && (
        <div className="mb-5 bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-sm flex items-center justify-between">
          <span>{statsError}</span>
          <button
            onClick={loadDashboard}
            className="text-blue-600 font-medium hover:underline"
          >
            Retry
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <MetricCard
          title="Total Villages"
          value={
            dashboardData
              ? dashboardData.totalVillages.toLocaleString()
              : "—"
          }
          description="Location records"
          icon="⌂"
        />

        <MetricCard
          title="Active Users"
          value={
            dashboardData
              ? dashboardData.activeUsers.toLocaleString()
              : "—"
          }
          description="Currently active users"
          icon="◉"
        />

        <MetricCard
          title="API Requests"
          value={
            dashboardData
              ? dashboardData.apiRequests.toLocaleString()
              : "—"
          }
          description="Today's requests"
          icon="↗"
        />

        <MetricCard
          title="Avg Response"
          value={
            dashboardData
              ? `${dashboardData.avgResponseTime.toFixed(2)} ms`
              : "—"
          }
          description="Average response time"
          icon="⚡"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-8">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold">
            API Requests
          </h3>
          <p className="text-sm text-slate-500">
            Requests over the last 7 days
          </p>

          <div className="h-72 mt-5">
            {apiRequestsData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={apiRequestsData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="requests"
                    stroke="#2563eb"
                    strokeWidth={3}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-slate-400">
                No API request data available
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold">
            Villages by State
          </h3>
          <p className="text-sm text-slate-500">
            Top states by village count
          </p>

          <div className="h-72 mt-5">
            {villagesByStateData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={villagesByStateData}
                  layout="vertical"
                  margin={{
                    top: 5,
                    right: 20,
                    left: 20,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    tickFormatter={(value) =>
                      Number(value).toLocaleString()
                    }
                  />
                  <YAxis
                    type="category"
                    dataKey="state"
                    width={125}
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip
                    formatter={(value) =>
                      Number(value).toLocaleString()
                    }
                  />
                  <Bar
                    dataKey="villages"
                    fill="#2563eb"
                    radius={[0, 5, 5, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-slate-400">
                No village statistics available
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-6 mt-8">
        <h3 className="text-lg font-semibold">
          Quick Village Search
        </h3>
        <p className="text-sm text-slate-500 mt-1 mb-5">
          Search imported village records
        </p>
        <VillageSearch />
      </div>

      <LocationHierarchy />
    </div>
  );
}

/* =========================
   METRIC CARD
========================= */

function MetricCard({
  title,
  value,
  description,
  icon,
}: {
  title: string;
  value: string;
  description: string;
  icon: string;
}) {

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">

      <div className="flex items-start justify-between">

        <div>

          <p className="text-sm text-slate-500">
            {title}
          </p>

          <h3 className="text-3xl font-bold text-slate-900 mt-2">
            {value}
          </h3>

          <p className="text-sm text-green-600 mt-2">
            {description}
          </p>

        </div>


        <div className="w-11 h-11 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-xl">
          {icon}
        </div>

      </div>

    </div>
  );
}


/* =========================
   VILLAGE SEARCH
========================= */

function VillageSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    const searchText = query.trim();

    if (!searchText) {
      setResults([]);
      setError("");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await searchVillages(searchText);

      const backendResults =
        Array.isArray(response)
          ? response
          : Array.isArray((response as any)?.data)
          ? (response as any).data
          : [];

      setResults(backendResults);
    } catch (err) {
      console.error("Village search error:", err);

      setResults([]);

      setError(
        "Unable to connect to the backend. Make sure Priya's API server is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <div>
      <div className="flex gap-3">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search village name, district, state or code..."
          className="flex-1 border border-slate-300 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500"
        />

        <button
          onClick={handleSearch}
          disabled={loading}
          className="bg-blue-600 text-white px-7 rounded-lg hover:bg-blue-700 disabled:bg-blue-300"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {error && (
        <div className="mt-4 bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {query.trim() && !loading && !error && (
        <div className="mt-4">
          {results.length > 0 ? (
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              {results.map((result, index) => {
                const hierarchy = result?.hierarchy || {};

                const villageName =
                  result?.label ||
                  hierarchy?.village ||
                  "Unknown village";

                const subDistrict =
                  hierarchy?.subDistrict || "";

                const district =
                  hierarchy?.district || "";

                const state =
                  hierarchy?.state || "";

                const fullAddress =
                  result?.fullAddress ||
                  [
                    villageName,
                    subDistrict,
                    district,
                    state,
                    "India",
                  ]
                    .filter(Boolean)
                    .join(", ");

                const villageCode =
                  result?.value?.replace(
                    "village_",
                    ""
                  ) || "N/A";

                return (
                  <div
                    key={
                      result?.value ||
                      `${villageName}-${index}`
                    }
                    className="p-4 border-b last:border-b-0 hover:bg-blue-50"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div className="min-w-0">
                        <p className="font-semibold text-slate-800">
                          {villageName}
                        </p>

                        <p className="text-sm text-slate-500 mt-1">
                          {fullAddress}
                        </p>
                      </div>

                      <div className="text-right shrink-0">
                        <p className="text-xs text-slate-400">
                          Village Code
                        </p>

                        <p className="text-sm font-medium text-slate-700">
                          {villageCode}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-5">
              <p className="font-medium">
                No villages found
              </p>

              <p className="text-sm text-slate-500 mt-1">
                Try another village, district, state or code.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


/* =========================
   LOCATION HIERARCHY
========================= */

function LocationHierarchy() {

  const [stateList, setStateList] =
    useState<State[]>([]);

  const [districtList, setDistrictList] =
    useState<District[]>([]);

  const [subDistrictList, setSubDistrictList] =
    useState<SubDistrict[]>([]);

  const [villageList, setVillageList] =
    useState<ApiVillage[]>([]);

  const [selectedStateId, setSelectedStateId] =
    useState("");

  const [selectedDistrictId, setSelectedDistrictId] =
    useState("");

  const [selectedSubDistrictId, setSelectedSubDistrictId] =
    useState("");

  const [selectedVillageId, setSelectedVillageId] =
    useState("");

  const [loadingStates, setLoadingStates] =
    useState(false);

  const [loadingDistricts, setLoadingDistricts] =
    useState(false);

  const [loadingSubDistricts, setLoadingSubDistricts] =
    useState(false);

  const [loadingVillages, setLoadingVillages] =
    useState(false);

  const [error, setError] =
    useState("");


  /* =========================
     LOAD STATES FROM BACKEND
  ========================= */

  useEffect(() => {

    const loadStates = async () => {

      try {
        setLoadingStates(true);
        setError("");

        const data = await getStates();

        setStateList(data);

      } catch (err) {
        console.error(err);

        setError(
          "Unable to load states. Please check the backend connection."
        );

        setStateList([]);

      } finally {
        setLoadingStates(false);
      }
    };

    loadStates();

  }, []);


  /* =========================
     LOAD DISTRICTS FROM BACKEND
  ========================= */

  useEffect(() => {

    if (!selectedStateId) {
      setDistrictList([]);
      setSubDistrictList([]);
      setVillageList([]);
      return;
    }


    const loadDistricts = async () => {

      try {
        setLoadingDistricts(true);
        setError("");

        const data = await getDistricts(
          selectedStateId
        );

        setDistrictList(data);

      } catch (err) {
        console.error(err);

        setError(
          "Unable to load districts."
        );

        setDistrictList([]);

      } finally {
        setLoadingDistricts(false);
      }
    };

    loadDistricts();

  }, [selectedStateId]);


  /* =========================
     LOAD SUB-DISTRICTS FROM BACKEND
  ========================= */

  useEffect(() => {

    if (!selectedDistrictId) {
      setSubDistrictList([]);
      setVillageList([]);
      return;
    }


    const loadSubDistricts = async () => {

      try {
        setLoadingSubDistricts(true);
        setError("");

        const data = await getSubDistricts(
          selectedDistrictId
        );

        setSubDistrictList(data);

      } catch (err) {
        console.error(err);

        setError(
          "Unable to load sub-districts."
        );

        setSubDistrictList([]);

      } finally {
        setLoadingSubDistricts(false);
      }
    };

    loadSubDistricts();

  }, [selectedDistrictId]);


  /* =========================
     LOAD VILLAGES FROM BACKEND
  ========================= */

  useEffect(() => {

    if (!selectedSubDistrictId) {
      setVillageList([]);
      return;
    }


    const loadVillages = async () => {

      try {
        setLoadingVillages(true);
        setError("");

        const data = await getVillagesBySubDistrict(
          selectedSubDistrictId
        );

        setVillageList(data);

      } catch (err) {
        console.error(err);

        setError(
          "Unable to load villages."
        );

        setVillageList([]);

      } finally {
        setLoadingVillages(false);
      }
    };

    loadVillages();

  }, [selectedSubDistrictId]);


  /* =========================
     SELECTED LOCATION DATA
  ========================= */

  const selectedState =
    stateList.find(
      (state) =>
        String(state.id) === selectedStateId
    );

  const selectedDistrict =
    districtList.find(
      (district) =>
        String(district.id) === selectedDistrictId
    );

  const selectedSubDistrict =
    subDistrictList.find(
      (subDistrict) =>
        String(subDistrict.id) === selectedSubDistrictId
    );

  const selectedVillage =
    villageList.find(
      (village) =>
        String(village.id) === selectedVillageId
    );


  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 mt-6">

      <div className="mb-6">

        <h3 className="text-lg font-semibold">
          Location Hierarchy
        </h3>

        <p className="text-sm text-slate-500 mt-1">
          Select a location step by step
        </p>

      </div>


      {error && (
        <div className="mb-5 bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-sm flex items-center justify-between">
          <span>{error}</span>

          <button
            type="button"
            onClick={() => window.location.reload()}
            className="text-blue-600 font-medium hover:underline"
          >
            Retry
          </button>
        </div>
      )}


      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">

        {/* STATE */}
        <div>

          <label className="block text-sm font-medium mb-2">
            State
          </label>

          <select
            value={selectedStateId}
            disabled={loadingStates}
            onChange={(e) => {

              setSelectedStateId(e.target.value);

              setSelectedDistrictId("");
              setSelectedSubDistrictId("");
              setSelectedVillageId("");

              setDistrictList([]);
              setSubDistrictList([]);
              setVillageList([]);

              setError("");
            }}
            className="w-full border border-slate-300 rounded-lg px-4 py-3 disabled:bg-slate-100"
          >

            <option value="">
              {loadingStates
                ? "Loading States..."
                : "Select State"}
            </option>

            {stateList.map((state) => (
              <option
                key={state.id}
                value={state.id}
              >
                {state.name}
              </option>
            ))}

          </select>

        </div>


        {/* DISTRICT */}
        <div>

          <label className="block text-sm font-medium mb-2">
            District
          </label>

          <select
            value={selectedDistrictId}
            disabled={
              !selectedStateId ||
              loadingDistricts
            }
            onChange={(e) => {

              setSelectedDistrictId(e.target.value);

              setSelectedSubDistrictId("");
              setSelectedVillageId("");

              setSubDistrictList([]);
              setVillageList([]);

              setError("");
            }}
            className="w-full border border-slate-300 rounded-lg px-4 py-3 disabled:bg-slate-100"
          >

            <option value="">
              {loadingDistricts
                ? "Loading Districts..."
                : "Select District"}
            </option>

            {districtList.map((district) => (
              <option
                key={district.id}
                value={district.id}
              >
                {district.name}
              </option>
            ))}

          </select>

        </div>


        {/* SUB-DISTRICT */}
        <div>

          <label className="block text-sm font-medium mb-2">
            Sub-District
          </label>

          <select
            value={selectedSubDistrictId}
            disabled={
              !selectedDistrictId ||
              loadingSubDistricts
            }
            onChange={(e) => {

              setSelectedSubDistrictId(
                e.target.value
              );

              setSelectedVillageId("");
              setVillageList([]);
              setError("");
            }}
            className="w-full border border-slate-300 rounded-lg px-4 py-3 disabled:bg-slate-100"
          >

            <option value="">
              {loadingSubDistricts
                ? "Loading Sub-Districts..."
                : "Select Sub-District"}
            </option>

            {subDistrictList.map(
              (subDistrict) => (
                <option
                  key={subDistrict.id}
                  value={subDistrict.id}
                >
                  {subDistrict.name}
                </option>
              )
            )}

          </select>

        </div>


        {/* VILLAGE */}
        <div>

          <label className="block text-sm font-medium mb-2">
            Village
          </label>

          <select
            value={selectedVillageId}
            disabled={
              !selectedSubDistrictId ||
              loadingVillages
            }
            onChange={(e) => {
              setSelectedVillageId(
                e.target.value
              );
              setError("");
            }}
            className="w-full border border-slate-300 rounded-lg px-4 py-3 disabled:bg-slate-100"
          >

            <option value="">
              {loadingVillages
                ? "Loading Villages..."
                : "Select Village"}
            </option>

            {villageList.map((village, index) => (
              <option
                key={
                  village.id ??
                  village.code ??
                  index
                }
                value={
                  village.id !== undefined
                    ? String(village.id)
                    : String(index)
                }
              >
                {village.name}
              </option>
            ))}

          </select>

        </div>

      </div>


      {selectedVillage && (

        <div className="mt-6 bg-blue-50 border border-blue-100 rounded-lg p-5">

          <h4 className="font-semibold text-blue-900">
            Selected Location
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mt-4">

            <div>
              <p className="text-xs text-slate-500">
                State
              </p>
              <p className="font-medium">
                {selectedVillage.state_name ??
                  selectedVillage.state ??
                  selectedState?.name ??
                  "-"}
              </p>
            </div>


            <div>
              <p className="text-xs text-slate-500">
                District
              </p>
              <p className="font-medium">
                {selectedVillage.district_name ??
                  selectedVillage.district ??
                  selectedDistrict?.name ??
                  "-"}
              </p>
            </div>


            <div>
              <p className="text-xs text-slate-500">
                Sub-District
              </p>
              <p className="font-medium">
                {selectedVillage.sub_district_name ??
                  selectedVillage.sub_district ??
                  selectedSubDistrict?.name ??
                  "-"}
              </p>
            </div>


            <div>
              <p className="text-xs text-slate-500">
                Village
              </p>
              <p className="font-medium">
                {selectedVillage.name}
              </p>
            </div>


            <div>
              <p className="text-xs text-slate-500">
                Village Code
              </p>
              <p className="font-medium">
                {selectedVillage.code ?? "-"}
              </p>
            </div>

          </div>

        </div>

      )}

    </div>
  );
}


/* =========================
   VILLAGES PAGE
========================= */

/* =========================
   VILLAGES PAGE
========================= */

function VillagesPage() {

  const [stateList, setStateList] = useState<State[]>([]);
  const [districtList, setDistrictList] = useState<District[]>([]);
  const [subDistrictList, setSubDistrictList] = useState<SubDistrict[]>([]);
  const [villageList, setVillageList] = useState<ApiVillage[]>([]);

  const [selectedStateId, setSelectedStateId] = useState("");
  const [selectedDistrictId, setSelectedDistrictId] = useState("");
  const [selectedSubDistrictId, setSelectedSubDistrictId] = useState("");

  const [villageSearch, setVillageSearch] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const VILLAGES_PER_PAGE = 50;

  const [loadingStates, setLoadingStates] = useState(false);
  const [loadingDistricts, setLoadingDistricts] = useState(false);
  const [loadingSubDistricts, setLoadingSubDistricts] = useState(false);
  const [loadingVillages, setLoadingVillages] = useState(false);
  const [error, setError] = useState("");

  /* =========================
     LOAD STATES
  ========================= */
  useEffect(() => {
    const loadStates = async () => {
      try {
        setLoadingStates(true);
        setError("");
        const data = await getStates();
        setStateList(data);
      } catch (err) {
        console.error(err);
        setError("Unable to load states. Please check the backend connection.");
      } finally {
        setLoadingStates(false);
      }
    };
    loadStates();
  }, []);

  /* =========================
     LOAD DISTRICTS
  ========================= */
  useEffect(() => {
    if (!selectedStateId) {
      setDistrictList([]);
      setSubDistrictList([]);
      setVillageList([]);
      setCurrentPage(1);
      return;
    }

    const loadDistricts = async () => {
      try {
        setLoadingDistricts(true);
        setError("");
        const data = await getDistricts(selectedStateId);
        setDistrictList(data);
      } catch (err) {
        console.error(err);
        setError("Unable to load districts.");
        setDistrictList([]);
      } finally {
        setLoadingDistricts(false);
      }
    };
    loadDistricts();
  }, [selectedStateId]);

  /* =========================
     LOAD SUB-DISTRICTS
  ========================= */
  useEffect(() => {
    if (!selectedDistrictId) {
      setSubDistrictList([]);
      setVillageList([]);
      setCurrentPage(1);
      return;
    }

    const loadSubDistricts = async () => {
      try {
        setLoadingSubDistricts(true);
        setError("");
        const data = await getSubDistricts(selectedDistrictId);
        setSubDistrictList(data);
      } catch (err) {
        console.error(err);
        setError("Unable to load sub-districts.");
        setSubDistrictList([]);
      } finally {
        setLoadingSubDistricts(false);
      }
    };
    loadSubDistricts();
  }, [selectedDistrictId]);

  /* =========================
     LOAD VILLAGES
  ========================= */
  useEffect(() => {
    if (!selectedSubDistrictId) {
      setVillageList([]);
      setCurrentPage(1);
      return;
    }

    const loadVillages = async () => {
      try {
        setLoadingVillages(true);
        setError("");
        const data = await getVillagesBySubDistrict(selectedSubDistrictId);
        setVillageList(data);
        setCurrentPage(1);
      } catch (err) {
        console.error(err);
        setError("Unable to load villages.");
        setVillageList([]);
      } finally {
        setLoadingVillages(false);
      }
    };
    loadVillages();
  }, [selectedSubDistrictId]);

  /* =========================
     FILTER + PAGINATION
  ========================= */
  const filteredVillages = villageList.filter((village) =>
    village.name
      .toLowerCase()
      .includes(villageSearch.trim().toLowerCase())
  );

  const totalRecords = filteredVillages.length;
  const totalPages = Math.max(1, Math.ceil(totalRecords / VILLAGES_PER_PAGE));

  const safeCurrentPage = Math.min(currentPage, totalPages);
  const startIndex = (safeCurrentPage - 1) * VILLAGES_PER_PAGE;
  const endIndex = Math.min(startIndex + VILLAGES_PER_PAGE, totalRecords);
  const visibleVillages = filteredVillages.slice(startIndex, endIndex);

  useEffect(() => {
    setCurrentPage(1);
  }, [villageSearch]);

  /* =========================
     GET SELECTED NAMES
  ========================= */
  const selectedState = stateList.find(
    (state) => String(state.id) === selectedStateId
  );

  const selectedDistrict = districtList.find(
    (district) => String(district.id) === selectedDistrictId
  );

  const selectedSubDistrict = subDistrictList.find(
    (subDistrict) => String(subDistrict.id) === selectedSubDistrictId
  );

  return (
    <div>
      {/* =========================
          PAGE HEADER
      ========================= */}
      <div className="mb-8">
        <h2 className="text-3xl font-bold">Village Master List</h2>
        <p className="text-slate-500 mt-1">
          Explore and verify imported village data
        </p>
      </div>

      {/* =========================
          LOCATION FILTERS
      ========================= */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="font-semibold text-lg mb-5">Location Filters</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* STATE */}
          <select
            value={selectedStateId}
            onChange={(e) => {
              setSelectedStateId(e.target.value);
              setSelectedDistrictId("");
              setSelectedSubDistrictId("");
              setDistrictList([]);
              setSubDistrictList([]);
              setVillageList([]);
              setVillageSearch("");
              setCurrentPage(1);
            }}
            className="border border-slate-300 rounded-lg px-4 py-3"
          >
            <option value="">
              {loadingStates ? "Loading States..." : "All States"}
            </option>
            {stateList.map((state) => (
              <option key={state.id} value={state.id}>
                {state.name}
              </option>
            ))}
          </select>

          {/* DISTRICT */}
          <select
            value={selectedDistrictId}
            disabled={!selectedStateId || loadingDistricts}
            onChange={(e) => {
              setSelectedDistrictId(e.target.value);
              setSelectedSubDistrictId("");
              setSubDistrictList([]);
              setVillageList([]);
              setVillageSearch("");
              setCurrentPage(1);
            }}
            className="border border-slate-300 rounded-lg px-4 py-3 disabled:bg-slate-100"
          >
            <option value="">
              {loadingDistricts ? "Loading Districts..." : "All Districts"}
            </option>
            {districtList.map((district) => (
              <option key={district.id} value={district.id}>
                {district.name}
              </option>
            ))}
          </select>

          {/* SUB-DISTRICT */}
          <select
            value={selectedSubDistrictId}
            disabled={!selectedDistrictId || loadingSubDistricts}
            onChange={(e) => {
              setSelectedSubDistrictId(e.target.value);
              setVillageList([]);
              setVillageSearch("");
              setCurrentPage(1);
            }}
            className="border border-slate-300 rounded-lg px-4 py-3 disabled:bg-slate-100"
          >
            <option value="">
              {loadingSubDistricts
                ? "Loading Sub-Districts..."
                : "All Sub-Districts"}
            </option>
            {subDistrictList.map((subDistrict) => (
              <option key={subDistrict.id} value={subDistrict.id}>
                {subDistrict.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* =========================
          ERROR MESSAGE
      ========================= */}
      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
          {error}
        </div>
      )}

      {/* =========================
          VILLAGE TABLE
      ========================= */}
      <div className="bg-white rounded-xl border border-slate-200 mt-6 overflow-hidden">
        <div className="p-6 border-b">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <h3 className="font-semibold">Village Records</h3>
              <p className="text-sm text-slate-500 mt-1">
                {loadingVillages
                  ? "Loading villages..."
                  : selectedSubDistrictId
                    ? `Total matching records: ${totalRecords.toLocaleString()}`
                    : "Select a location to view villages"}
              </p>
            </div>

            {selectedSubDistrictId && (
              <div className="relative w-full lg:w-80">
                <input
                  type="text"
                  value={villageSearch}
                  onChange={(e) => setVillageSearch(e.target.value)}
                  placeholder="Search Village Name"
                  className="w-full border border-slate-300 rounded-lg px-4 py-3 pr-10 outline-none focus:ring-2 focus:ring-blue-500"
                />
                {villageSearch && (
                  <button
                    type="button"
                    onClick={() => setVillageSearch("")}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
                    aria-label="Clear village search"
                  >
                    ×
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                <th className="text-left px-6 py-4 text-sm font-semibold">Village Code</th>
                <th className="text-left px-6 py-4 text-sm font-semibold">Village Name</th>
                <th className="text-left px-6 py-4 text-sm font-semibold">Sub-District</th>
                <th className="text-left px-6 py-4 text-sm font-semibold">District</th>
                <th className="text-left px-6 py-4 text-sm font-semibold">State</th>
              </tr>
            </thead>

            <tbody>
              {loadingVillages && (
                <tr>
                  <td colSpan={5} className="px-6 py-10 text-center text-slate-500">
                    Loading villages...
                  </td>
                </tr>
              )}

              {!loadingVillages && visibleVillages.map((village, index) => (
                <tr
                  key={village.id ?? village.code ?? index}
                  className="border-t hover:bg-slate-50"
                >
                  <td className="px-6 py-4 text-sm">{village.code ?? "-"}</td>
                  <td className="px-6 py-4 font-medium">{village.name}</td>
                  <td className="px-6 py-4 text-sm">
                    {village.sub_district_name ??
                      village.sub_district ??
                      selectedSubDistrict?.name ??
                      "-"}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {village.district_name ??
                      village.district ??
                      selectedDistrict?.name ??
                      "-"}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {village.state_name ??
                      village.state ??
                      selectedState?.name ??
                      "-"}
                  </td>
                </tr>
              ))}

              {!loadingVillages && selectedSubDistrictId && totalRecords === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-10 text-center text-slate-500">
                    {villageSearch
                      ? `No villages found for "${villageSearch}".`
                      : "No villages found."}
                  </td>
                </tr>
              )}

              {!selectedSubDistrictId && (
                <tr>
                  <td colSpan={5} className="px-6 py-10 text-center text-slate-500">
                    Select a State, District and Sub-District to view villages.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* =========================
            PAGINATION
        ========================= */}
        {selectedSubDistrictId && !loadingVillages && totalRecords > 0 && (
          <div className="border-t border-slate-200 px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <p className="text-sm text-slate-600">
              Showing <span className="font-semibold">{startIndex + 1}</span>–
              <span className="font-semibold">{endIndex}</span> of {totalRecords.toLocaleString()}
            </p>

            <div className="flex items-center gap-3">
              <button
                type="button"
                disabled={safeCurrentPage === 1}
                onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                className="px-4 py-2 rounded-lg border border-slate-300 text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition"
              >
                ← Previous
              </button>

              <span className="text-sm text-slate-600 min-w-[90px] text-center">
                Page {safeCurrentPage} of {totalPages}
              </span>

              <button
                type="button"
                disabled={safeCurrentPage >= totalPages}
                onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                className="px-4 py-2 rounded-lg border border-slate-300 text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition"
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


function UsersPage({ onNotify }: { onNotify?: (title: string, message: string, type?: NotificationType) => void }) {
  const [tab, setTab] = useState<"users" | "keys">("users");
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [keysLoading, setKeysLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [planFilter, setPlanFilter] = useState("All");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [selectedUser, setSelectedUser] = useState<AdminUserItem | null>(null);
  const [notes, setNotes] = useState("");
  const [savingUser, setSavingUser] = useState(false);
  const [stateAccess, setStateAccess] = useState<UserStateAccess | null>(null);
  const [stateLoading, setStateLoading] = useState(false);
  const [selectedStates, setSelectedStates] = useState<number[]>([]);
  const [rotatingId, setRotatingId] = useState<number | null>(null);
  const [updatingKeyId, setUpdatingKeyId] = useState<number | null>(null);
  const [rotatedSecret, setRotatedSecret] = useState<string | null>(null);
  const [showCreateKey, setShowCreateKey] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyRate, setNewKeyRate] = useState("1000");
  const [creatingKey, setCreatingKey] = useState(false);
  const [newKeySecret, setNewKeySecret] = useState<string | null>(null);
  const [newKeyValue, setNewKeyValue] = useState<string | null>(null);
  const [rotatedKeyValue, setRotatedKeyValue] = useState<string | null>(null);
  const [copiedCredential, setCopiedCredential] = useState<string | null>(null);
  const [userLogs, setUserLogs] = useState<AdminLog[]>([]);
  const [userLogsLoading, setUserLogsLoading] = useState(false);
  const [userLogsError, setUserLogsError] = useState("");
  const [userAction, setUserAction] = useState<{ id: number; type: "approve" | "suspend" | "delete" | "reject" } | null>(null);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await getAdminUsers({
        search: search.trim() || undefined,
        status: statusFilter === "All" ? undefined : statusFilter,
        plan: planFilter === "All" ? undefined : planFilter,
        page: 1,
        page_size: 100,
      });
      setUsers(data.items || []);
      setSelectedIds([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load users.");
    } finally {
      setLoading(false);
    }
  };

  const loadKeys = async () => {
    try {
      setKeysLoading(true);
      const data = await getApiKeys();
      setApiKeys(Array.isArray(data) ? data as ApiKeyItem[] : (data as any)?.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load API keys.");
      setApiKeys([]);
    } finally {
      setKeysLoading(false);
    }
  };

  useEffect(() => { loadUsers(); }, [statusFilter, planFilter]);
  useEffect(() => { loadKeys(); }, []);

  const openUser = async (user: AdminUserItem) => {
    setSelectedUser(user);
    setNotes(user.admin_notes || "");
    setStateAccess(null);
    setStateLoading(true);
    setUserLogs([]);
    setUserLogsError("");
    try {
      const access = await getUserStateAccess(user.id);
      setStateAccess(access);
      setSelectedStates(access.granted_state_ids || []);
      await loadUserRequestHistory(user.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load state access.");
    } finally {
      setStateLoading(false);
    }
  };

  const saveUser = async (patch: Record<string, unknown>) => {
    if (!selectedUser) return;
    try {
      setSavingUser(true);
      const updated = await updateAdminUser(selectedUser.id, patch);
      setUsers(prev => prev.map(u => u.id === updated.id ? updated : u));
      setSelectedUser(updated);
      setNotes(updated.admin_notes || "");
      onNotify?.("User updated", `${updated.email} was updated successfully.`, "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to update user.";
      setError(message);
      onNotify?.("User update failed", message, "error");
    } finally {
      setSavingUser(false);
    }
  };

  const approveUser = async (user: AdminUserItem) => {
    try {
      setUserAction({ id: user.id, type: "approve" });
      const updated = await approveAdminUser(user.id, { plan: user.plan || "free" });
      setUsers(prev => prev.map(u => u.id === updated.id ? updated : u));
      onNotify?.("User approved", `${updated.email} is now approved.`, "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to approve user.";
      setError(message);
      onNotify?.("User approval failed", message, "error");
    } finally {
      setUserAction(null);
    }
  };

  const rejectUser = async (user: AdminUserItem) => {
    const reason = window.prompt("Rejection reason:", "Application rejected by administrator.");
    if (!reason) return;
    try {
      setUserAction({ id: user.id, type: "reject" });
      const updated = await rejectAdminUser(user.id, { reason });
      setUsers(prev => prev.map(u => u.id === updated.id ? updated : u));
      onNotify?.("User rejected", `${updated.email} was rejected.`, "warning");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to reject user.";
      setError(message);
      onNotify?.("User rejection failed", message, "error");
    } finally {
      setUserAction(null);
    }
  };

  const suspendOrActivate = async (user: AdminUserItem) => {
    const active = user.status === "active";
    try {
      setUserAction({ id: user.id, type: "suspend" });
      const updated = await updateAdminUser(user.id, {
        status: active ? "suspended" : "active",
        is_active: !active,
      });
      setUsers(prev => prev.map(u => u.id === updated.id ? updated : u));
      if (selectedUser?.id === updated.id) setSelectedUser(updated);
      onNotify?.(active ? "User suspended" : "User activated", `${updated.email} is now ${updated.status}.`, "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to change user status.";
      setError(message);
      onNotify?.("User status change failed", message, "error");
    } finally {
      setUserAction(null);
    }
  };

  const deleteUser = async (user: AdminUserItem) => {
    if (!window.confirm(`Delete ${user.email}? This cannot be undone.`)) return;
    try {
      setUserAction({ id: user.id, type: "delete" });
      await deleteAdminUser(user.id);
      setUsers(prev => prev.filter(u => u.id !== user.id));
      setSelectedIds(prev => prev.filter(id => id !== user.id));
      if (selectedUser?.id === user.id) setSelectedUser(null);
      onNotify?.("User deleted", `${user.email} was deleted successfully.`, "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to delete user.";
      setError(message);
      onNotify?.("User deletion failed", message, "error");
    } finally {
      setUserAction(null);
    }
  };

  const bulkAction = async (action: "approve" | "suspend" | "delete") => {
    if (!selectedIds.length) return;
    if (action === "delete" && !window.confirm(`Delete ${selectedIds.length} selected users?`)) return;
    try {
      setLoading(true);
      for (const id of selectedIds) {
        if (action === "approve") await approveAdminUser(id, { plan: "free" });
        if (action === "suspend") await updateAdminUser(id, { status: "suspended", is_active: false });
        if (action === "delete") await deleteAdminUser(id);
      }
      await loadUsers();
      onNotify?.("Bulk action completed", `${selectedIds.length} user(s) were ${action}d.`, "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Bulk action failed.";
      setError(message);
      onNotify?.("Bulk action failed", message, "error");
      setLoading(false);
    }
  };

  const loadUserRequestHistory = async (userId?: number) => {
    const targetUserId = userId ?? selectedUser?.id;
    if (!targetUserId) return;

    try {
      setUserLogsLoading(true);
      setUserLogsError("");

      // Request history is scoped through API keys owned by this user.
      // The admin logs endpoint supports api_key_id filtering.
      const keysResponse = await getApiKeys();
      const allKeys: ApiKeyItem[] = Array.isArray(keysResponse)
        ? (keysResponse as ApiKeyItem[])
        : ((keysResponse as any)?.items || []);

      const ownedKeys = allKeys.filter(
        (key) => Number((key as any).user_id) === Number(targetUserId)
      );

      if (ownedKeys.length === 0) {
        setUserLogs([]);
        return;
      }

      const results = await Promise.all(
        ownedKeys.map((key) =>
          getAdminLogs({ api_key_id: key.id, page: 1, page_size: 100 })
        )
      );

      const merged = results
        .flatMap((result) => result.items || [])
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() -
            new Date(a.created_at).getTime()
        );

      setUserLogs(merged.slice(0, 50));
    } catch (err) {
      setUserLogs([]);
      setUserLogsError(
        err instanceof Error
          ? err.message
          : "Unable to load request history."
      );
    } finally {
      setUserLogsLoading(false);
    }
  };

  const saveStateAccess = async () => {
    if (!selectedUser || !stateAccess) return;
    try {
      setStateLoading(true);
      await updateUserStateAccess(selectedUser.id, { state_ids: selectedStates, revoke: false });
      const refreshed = await getUserStateAccess(selectedUser.id);
      setStateAccess(refreshed);
      setSelectedStates(refreshed.granted_state_ids || []);
      onNotify?.("State access updated", `State access for ${selectedUser.email} was saved.`, "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to update state access.";
      setError(message);
      onNotify?.("State access update failed", message, "error");
    } finally {
      setStateLoading(false);
    }
  };

  const copyCredential = async (value: string, type: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedCredential(type);
      window.setTimeout(() => setCopiedCredential(null), 2000);
    } catch {
      setCopiedCredential(null);
    }
  };

  const createKey = async () => {
    if (!newKeyName.trim()) return;
    try {
      setCreatingKey(true);
      const result = await createAdminApiKey(newKeyName.trim(), Number(newKeyRate) || 1000);
      setNewKeyValue(result.key || null);
      setNewKeySecret(result.secret || null);
      setNewKeyName("");
      await loadKeys();
      onNotify?.("API key created", `API key "${result.name || newKeyName.trim()}" was created successfully.`, "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to create API key.";
      setError(message);
      onNotify?.("API key creation failed", message, "error");
    } finally {
      setCreatingKey(false);
    }
  };

  const rotateKey = async (keyId: number) => {
    if (!window.confirm("Rotate this API key? The current key will be invalidated immediately.")) return;
    try {
      setRotatingId(keyId);
      const result = await rotateApiKey(keyId);
      setRotatedKeyValue(result.key || result.api_key || null);
      setRotatedSecret(result.secret || result.api_secret || null);
      await loadKeys();
      onNotify?.("API key rotated", "The old API key was deactivated and a new key was generated.", "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to rotate API key.";
      setError(message);
      onNotify?.("API key rotation failed", message, "error");
    } finally {
      setRotatingId(null);
    }
  };

  const toggleKey = async (key: ApiKeyItem) => {
    try {
      setUpdatingKeyId(key.id);
      await updateAdminApiKey(key.id, { is_active: !key.is_active });
      await loadKeys();
      onNotify?.(key.is_active ? "API key deactivated" : "API key activated", `API key "${key.name}" is now ${key.is_active ? "inactive" : "active"}.`, "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to update API key.";
      setError(message);
      onNotify?.("API key update failed", message, "error");
    } finally {
      setUpdatingKeyId(null);
    }
  };

  const allSelected = users.length > 0 && selectedIds.length === users.length;

  // Only show API keys that are explicitly owned by the selected user.
  // Never fall back to all keys here, because that would expose other users' credentials.
  const selectedUserKeys = selectedUser
    ? apiKeys.filter(
        (key) => Number((key as any).user_id) === Number(selectedUser.id)
      )
    : [];

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-3xl font-bold">Users & API Access</h2>
        <p className="text-slate-500 mt-1">Manage registered users, approvals, plans and API credentials.</p>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 flex justify-between gap-4">
          <span>{error}</span>
          <button onClick={() => setError("")} className="font-medium">Dismiss</button>
        </div>
      )}

      <div className="flex gap-2 mb-6 border-b border-slate-200">
        <button onClick={() => setTab("users")} className={`px-5 py-3 font-medium border-b-2 ${tab === "users" ? "border-blue-600 text-blue-600" : "border-transparent text-slate-500"}`}>Users</button>
        <button
  onClick={() => {
    setSelectedUser(null);
    setTab("keys");
  }}
  className="px-3 py-2 border rounded-lg text-sm"
>
  Manage API Keys
</button>
      </div>

      {tab === "users" ? (
        <>
          <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <input value={search} onChange={e => setSearch(e.target.value)} onKeyDown={e => { if (e.key === "Enter") loadUsers(); }} placeholder="Search name, email or business" className="px-4 py-2.5 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-200" />
              <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="px-4 py-2.5 border border-slate-300 rounded-lg">
                <option value="All">All statuses</option><option value="pending_approval">Pending</option><option value="active">Active</option><option value="suspended">Suspended</option><option value="rejected">Rejected</option>
              </select>
              <select value={planFilter} onChange={e => setPlanFilter(e.target.value)} className="px-4 py-2.5 border border-slate-300 rounded-lg">
                <option value="All">All plans</option><option value="free">Free</option><option value="premium">Premium</option><option value="pro">Pro</option><option value="unlimited">Unlimited</option>
              </select>
            </div>
            <div className="flex flex-wrap gap-2 mt-4">
              <button onClick={loadUsers} className="bg-blue-600 text-white px-4 py-2 rounded-lg">Search</button>
              <button disabled={!selectedIds.length} onClick={() => bulkAction("approve")} className="px-4 py-2 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 active:bg-emerald-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed">✓ Approve selected</button>
              <button disabled={!selectedIds.length} onClick={() => bulkAction("suspend")} className="px-4 py-2 rounded-lg bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100 active:bg-amber-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed">⏸ Suspend selected</button>
              <button disabled={!selectedIds.length} onClick={() => bulkAction("delete")} className="px-4 py-2 rounded-lg bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 active:bg-red-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed">🗑 Delete selected</button>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50"><tr>
                  <th className="px-4 py-4"><input type="checkbox" checked={allSelected} onChange={e => setSelectedIds(e.target.checked ? users.map(u => u.id) : [])} /></th>
                  <th className="text-left px-4 py-4 text-sm font-semibold">User</th><th className="text-left px-4 py-4 text-sm font-semibold">Business</th><th className="text-left px-4 py-4 text-sm font-semibold">Plan</th><th className="text-left px-4 py-4 text-sm font-semibold">Status</th><th className="text-left px-4 py-4 text-sm font-semibold">Created</th><th className="text-left px-4 py-4 text-sm font-semibold">Actions</th>
                </tr></thead>
                <tbody>
                  {loading ? <tr><td colSpan={7} className="px-6 py-10 text-center text-slate-500">Loading users...</td></tr> : users.length === 0 ? <tr><td colSpan={7} className="px-6 py-10 text-center text-slate-500">No users found.</td></tr> : users.map(user => (
                    <tr key={user.id} className="border-t hover:bg-slate-50">
                      <td className="px-4 py-4"><input type="checkbox" checked={selectedIds.includes(user.id)} onChange={e => setSelectedIds(prev => e.target.checked ? [...prev, user.id] : prev.filter(id => id !== user.id))} /></td>
                      <td className="px-4 py-4"><button onClick={() => openUser(user)} className="text-left"><div className="font-medium text-slate-800">{user.full_name}</div><div className="text-sm text-slate-500">{user.email}</div></button></td>
                      <td className="px-4 py-4 text-sm">{user.business_name || "—"}</td>
                      <td className="px-4 py-4"><span className="px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-medium capitalize">{user.plan}</span></td>
                      <td className="px-4 py-4"><span className={`px-2.5 py-1 rounded-full text-xs font-medium ${user.status === "active" ? "bg-green-50 text-green-700" : user.status === "pending_approval" ? "bg-amber-50 text-amber-700" : "bg-slate-100 text-slate-700"}`}>{user.status.replaceAll("_", " ")}</span></td>
                      <td className="px-4 py-4 text-sm text-slate-600">{new Date(user.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-4">
  <div className="flex flex-wrap gap-2">
    <button
      type="button"
      onClick={() => openUser(user)}
      className="px-3 py-1.5 rounded-lg text-sm font-medium bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 active:bg-blue-200 active:scale-95 transition-all"
    >
      👁 View
    </button>
    {user.status !== "active" && (
      <button
        type="button"
        disabled={userAction?.id === user.id}
        onClick={() => approveUser(user)}
        className="px-3 py-1.5 rounded-lg text-sm font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 active:bg-emerald-200 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {userAction?.id === user.id && userAction.type === "approve" ? "⏳ Approving..." : "✓ Approve"}
      </button>
    )}
    <button
      type="button"
      disabled={userAction?.id === user.id}
      onClick={() => suspendOrActivate(user)}
      className={`px-3 py-1.5 rounded-lg text-sm font-medium border active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed ${user.status === "active" ? "bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100 active:bg-amber-200" : "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100 active:bg-emerald-200"}`}
    >
      {userAction?.id === user.id && userAction.type === "suspend"
        ? (user.status === "active" ? "⏳ Suspending..." : "⏳ Activating...")
        : (user.status === "active" ? "⏸ Suspend" : "✓ Activate")}
    </button>
    <button
      type="button"
      disabled={userAction?.id === user.id}
      onClick={() => deleteUser(user)}
      className="px-3 py-1.5 rounded-lg text-sm font-medium bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 active:bg-red-200 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {userAction?.id === user.id && userAction.type === "delete" ? "⏳ Deleting..." : "🗑 Delete"}
    </button>
  </div>
</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5 flex flex-wrap items-center justify-between gap-4">
            <div><h3 className="font-semibold text-lg">API Keys</h3><p className="text-sm text-slate-500 mt-1">Create, disable and rotate administrator-managed API credentials.</p></div>
            <button onClick={() => setShowCreateKey(v => !v)} className="bg-blue-600 text-white px-4 py-2.5 rounded-lg">{showCreateKey ? "Close" : "Create API Key"}</button>
          </div>
          {showCreateKey && <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5"><div className="grid grid-cols-1 md:grid-cols-3 gap-3"><input value={newKeyName} onChange={e => setNewKeyName(e.target.value)} placeholder="Key name" className="px-4 py-2.5 border rounded-lg"/><input type="number" min="1" value={newKeyRate} onChange={e => setNewKeyRate(e.target.value)} placeholder="Rate limit" className="px-4 py-2.5 border rounded-lg"/><button disabled={creatingKey || !newKeyName.trim()} onClick={createKey} className="bg-slate-900 text-white rounded-lg disabled:opacity-40">{creatingKey ? "Creating..." : "Create"}</button></div></div>}
          {(newKeyValue || newKeySecret || rotatedKeyValue || rotatedSecret) && (
            <div className="mb-5 bg-amber-50 border border-amber-200 rounded-xl p-5">
              <h3 className="font-semibold text-amber-900">New API credentials</h3>
              <p className="text-sm text-amber-800 mt-1">
                Copy both credentials now. The secret may not be shown again.
              </p>

              {(newKeyValue || rotatedKeyValue) && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-slate-700 mb-2">API Key</p>
                  <div className="flex gap-2">
                    <code className="flex-1 bg-white border border-amber-200 rounded-lg p-3 break-all">
                      {newKeyValue || rotatedKeyValue}
                    </code>
                    <button
                      type="button"
                      onClick={() => copyCredential(newKeyValue || rotatedKeyValue || "", "api-key")}
                      className="px-4 py-2 border border-amber-300 rounded-lg bg-white text-sm font-medium hover:bg-amber-100"
                    >
                      {copiedCredential === "api-key" ? "Copied" : "Copy"}
                    </button>
                  </div>
                </div>
              )}

              {(newKeySecret || rotatedSecret) && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-slate-700 mb-2">API Secret</p>
                  <div className="flex gap-2">
                    <code className="flex-1 bg-white border border-amber-200 rounded-lg p-3 break-all">
                      {newKeySecret || rotatedSecret}
                    </code>
                    <button
                      type="button"
                      onClick={() => copyCredential(newKeySecret || rotatedSecret || "", "api-secret")}
                      className="px-4 py-2 border border-amber-300 rounded-lg bg-white text-sm font-medium hover:bg-amber-100"
                    >
                      {copiedCredential === "api-secret" ? "Copied" : "Copy"}
                    </button>
                  </div>
                </div>
              )}

              <button
                type="button"
                onClick={() => {
                  setNewKeyValue(null);
                  setNewKeySecret(null);
                  setRotatedKeyValue(null);
                  setRotatedSecret(null);
                  setCopiedCredential(null);
                }}
                className="mt-4 text-sm underline"
              >
                Close
              </button>
            </div>
          )}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-5 py-4 text-sm font-semibold">ID</th>
                    <th className="text-left px-5 py-4 text-sm font-semibold">Name</th>
                    <th className="text-left px-5 py-4 text-sm font-semibold">API Key</th>
                    <th className="text-left px-5 py-4 text-sm font-semibold">Status</th>
                    <th className="text-left px-5 py-4 text-sm font-semibold">Rate Limit</th>
                    <th className="text-left px-5 py-4 text-sm font-semibold">Requests</th>
                    <th className="text-left px-5 py-4 text-sm font-semibold">Created</th>
                    <th className="text-left px-5 py-4 text-sm font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {keysLoading ? (
                    <tr>
                      <td colSpan={8} className="px-6 py-10 text-center text-slate-500">
                        Loading API keys...
                      </td>
                    </tr>
                  ) : apiKeys.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="px-6 py-10 text-center text-slate-500">
                        No API keys found.
                      </td>
                    </tr>
                  ) : (
                    apiKeys.map(key => (
                      <tr key={key.id} className="border-t hover:bg-slate-50">
                        <td className="px-5 py-4 text-sm">{key.id}</td>
                        <td className="px-5 py-4 font-medium">{key.name}</td>
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-2 min-w-[260px]">
                            <code className="text-xs bg-slate-50 border border-slate-200 rounded px-2 py-1 break-all">
                              {key.key || "Not available"}
                            </code>
                            {key.key && (
                              <button
                                type="button"
                                onClick={() => copyCredential(key.key, `table-key-${key.id}`)}
                                className="shrink-0 px-2.5 py-1.5 border rounded-lg text-xs bg-white hover:bg-slate-50"
                              >
                                {copiedCredential === `table-key-${key.id}` ? "Copied" : "Copy"}
                              </button>
                            )}
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <span className={`px-2.5 py-1 rounded-full text-xs ${key.is_active ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
                            {key.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-sm">{key.rate_limit}</td>
                        <td className="px-5 py-4 text-sm">{key.total_requests.toLocaleString()}</td>
                        <td className="px-5 py-4 text-sm">{new Date(key.created_at).toLocaleString()}</td>
                        <td className="px-5 py-4">
                          <div className="flex gap-2">
                            <button
                              disabled={updatingKeyId === key.id}
                              onClick={() => toggleKey(key)}
                              className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed ${key.is_active ? "bg-red-50 text-red-700 border-red-200 hover:bg-red-100" : "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100"}`}
                            >
                              {updatingKeyId === key.id ? "⏳ Updating..." : key.is_active ? "Revoke" : "✓ Activate"}
                            </button>
                            <button
                              disabled={rotatingId === key.id}
                              onClick={() => rotateKey(key.id)}
                              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 active:bg-blue-200 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {rotatingId === key.id ? "⏳ Rotating..." : "↻ Rotate"}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {selectedUser && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-5xl max-h-[92vh] overflow-y-auto">
            <div className="p-6 border-b flex items-center justify-between sticky top-0 bg-white z-10">
              <div><h3 className="text-xl font-bold">User Details</h3><p className="text-sm text-slate-500">{selectedUser.email}</p></div>
              <button onClick={() => setSelectedUser(null)} className="text-slate-500 text-xl">×</button>
            </div>
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div><label className="text-xs text-slate-500">Full name</label><p className="font-medium">{selectedUser.full_name}</p></div>
                <div><label className="text-xs text-slate-500">Business</label><p className="font-medium">{selectedUser.business_name || "—"}</p></div>
                <div><label className="text-xs text-slate-500">Phone</label><p>{selectedUser.phone || "—"}</p></div>
                <div><label className="text-xs text-slate-500">GST</label><p>{selectedUser.gst_number || "—"}</p></div>
                <div><label className="text-xs text-slate-500">Created</label><p>{new Date(selectedUser.created_at).toLocaleString()}</p></div>
                <div><label className="text-xs text-slate-500">Last login</label><p>{selectedUser.last_login_at ? new Date(selectedUser.last_login_at).toLocaleString() : "Never"}</p></div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div><label className="block text-sm font-medium mb-1">Plan</label><select value={selectedUser.plan} onChange={e => saveUser({ plan: e.target.value })} disabled={savingUser} className="w-full border rounded-lg px-3 py-2"><option value="free">Free</option><option value="premium">Premium</option><option value="pro">Pro</option><option value="unlimited">Unlimited</option></select></div>
                <div><label className="block text-sm font-medium mb-1">Status</label><select value={selectedUser.status} onChange={e => saveUser({ status: e.target.value, is_active: e.target.value === "active" })} disabled={savingUser} className="w-full border rounded-lg px-3 py-2"><option value="pending_approval">Pending approval</option><option value="active">Active</option><option value="suspended">Suspended</option><option value="rejected">Rejected</option></select></div>
              </div>
              <div><label className="block text-sm font-medium mb-1">Admin notes</label><textarea value={notes} onChange={e => setNotes(e.target.value)} rows={3} className="w-full border rounded-lg px-3 py-2"/><button onClick={() => saveUser({ admin_notes: notes })} disabled={savingUser} className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg">Save notes</button></div>

              <div className="border-t pt-5">
                <div className="flex items-center justify-between mb-3"><div><h4 className="font-semibold">API Keys</h4><p className="text-xs text-slate-500 mt-1">Current admin API-key records.</p></div><button onClick={() => setTab("keys")} className="px-3 py-2 border rounded-lg text-sm">Manage API Keys</button></div>
                {keysLoading ? (
                  <p className="text-sm text-slate-500">Loading API keys...</p>
                ) : selectedUserKeys.length ? (
                  <div className="overflow-x-auto border rounded-lg">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="text-left px-4 py-3">Name</th>
                          <th className="text-left px-4 py-3">Status</th>
                          <th className="text-left px-4 py-3">Requests</th>
                          <th className="text-left px-4 py-3">Rate limit</th>
                          <th className="text-left px-4 py-3">Created</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedUserKeys.map((key) => (
                          <tr key={key.id} className="border-t">
                            <td className="px-4 py-3 font-medium">{key.name}</td>
                            <td className="px-4 py-3">{key.is_active ? "Active" : "Inactive"}</td>
                            <td className="px-4 py-3">{Number(key.total_requests || 0).toLocaleString()}</td>
                            <td className="px-4 py-3">{Number(key.rate_limit || 0).toLocaleString()}</td>
                            <td className="px-4 py-3">{new Date(key.created_at).toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="border rounded-lg p-4 text-sm text-slate-500">
                    No API keys assigned to this user.
                  </div>
                )}
              </div>

              <div className="border-t pt-5">
                <div className="flex items-center justify-between mb-3"><div><h4 className="font-semibold">Request History</h4><p className="text-xs text-slate-500 mt-1">Recent requests made using this user's API keys.</p></div><button onClick={() => loadUserRequestHistory()} disabled={userLogsLoading} className="px-3 py-2 border rounded-lg text-sm">{userLogsLoading ? "Loading..." : "Refresh"}</button></div>
                {userLogsError && <div className="mb-3 bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">{userLogsError}</div>}
                {userLogsLoading ? <p className="text-sm text-slate-500">Loading request history...</p> : userLogs.length ? <div className="overflow-x-auto border rounded-lg"><table className="w-full text-sm"><thead className="bg-slate-50"><tr><th className="text-left px-4 py-3">Timestamp</th><th className="text-left px-4 py-3">Method</th><th className="text-left px-4 py-3">Endpoint</th><th className="text-left px-4 py-3">Response</th><th className="text-left px-4 py-3">Status</th><th className="text-left px-4 py-3">IP</th></tr></thead><tbody>{userLogs.slice(0,20).map(log => <tr key={log.id} className="border-t"><td className="px-4 py-3 whitespace-nowrap">{new Date(log.created_at).toLocaleString()}</td><td className="px-4 py-3">{log.method}</td><td className="px-4 py-3 font-mono text-xs">{log.path}</td><td className="px-4 py-3">{Number(log.duration_ms || 0).toFixed(2)} ms</td><td className="px-4 py-3">{log.status_code}</td><td className="px-4 py-3 font-mono text-xs">{log.ip_address || "—"}</td></tr>)}</tbody></table></div> : <div className="border rounded-lg p-4 text-sm text-slate-500">No request history found.</div>}
              </div>

              <div className="border-t pt-5"><h4 className="font-semibold mb-2">State access</h4>{stateLoading ? <p className="text-sm text-slate-500">Loading state access...</p> : stateAccess ? <><p className="text-sm text-slate-500 mb-3">{stateAccess.has_full_access ? "Full access: no state restrictions are configured." : `${selectedStates.length} state(s) explicitly granted.`}</p><div className="max-h-48 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-2 border rounded-lg p-3">{stateAccess.states.map(state => <label key={state.id} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={selectedStates.includes(state.id)} onChange={e => setSelectedStates(prev => e.target.checked ? [...prev, state.id] : prev.filter(id => id !== state.id))}/>{state.name} ({state.code})</label>)}</div><button onClick={saveStateAccess} disabled={stateLoading} className="mt-3 px-4 py-2 border rounded-lg">Save state access</button></> : null}</div>
              <div className="flex flex-wrap gap-2 pt-2"><button onClick={() => approveUser(selectedUser)} className="px-4 py-2 border rounded-lg">Approve</button><button onClick={() => suspendOrActivate(selectedUser)} className="px-4 py-2 border rounded-lg">{selectedUser.status === "active" ? "Suspend" : "Activate"}</button><button onClick={() => rejectUser(selectedUser)} className="px-4 py-2 border rounded-lg">Reject</button><button onClick={() => deleteUser(selectedUser)} className="px-4 py-2 border border-red-200 text-red-600 rounded-lg">Delete</button></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


/* =========================
   API LOGS
========================= */

function ApiLogsPage() {
  const [logs, setLogs] = useState<AdminLog[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [stats, setStats] = useState({
    successful: 0,
    rateLimited: 0,
    averageResponse: 0,
  });

  const itemsPerPage = 20;

  useEffect(() => {
    let cancelled = false;

    const loadLogs = async () => {
      setLoading(true);
      setError("");

      try {
        const status =
          statusFilter === "All" ? undefined : Number(statusFilter);

        const [pageResult, allResult, successResult, rateLimitResult] =
          await Promise.all([
            getAdminLogs({
              search: search.trim() || undefined,
              status,
              page: currentPage,
              page_size: itemsPerPage,
            }),
            getAdminLogs({
              search: search.trim() || undefined,
              status,
              page: 1,
              page_size: 100,
            }),
            status === undefined
              ? getAdminLogs({
                  search: search.trim() || undefined,
                  status: 200,
                  page: 1,
                  page_size: 100,
                })
              : Promise.resolve(null),
            status === undefined
              ? getAdminLogs({
                  search: search.trim() || undefined,
                  status: 429,
                  page: 1,
                  page_size: 100,
                })
              : Promise.resolve(null),
          ]);

        if (cancelled) return;

        setLogs(pageResult.items);
        setTotalCount(pageResult.count);

        const durations = allResult.items.map((item) => item.duration_ms);
        const averageResponse = durations.length
          ? Math.round(
              durations.reduce((sum, value) => sum + value, 0) /
                durations.length
            )
          : 0;

        if (status === undefined) {
          setStats({
            successful: successResult?.count ?? 0,
            rateLimited: rateLimitResult?.count ?? 0,
            averageResponse,
          });
        } else {
          setStats({
            successful: status === 200 ? pageResult.count : 0,
            rateLimited: status === 429 ? pageResult.count : 0,
            averageResponse,
          });
        }
      } catch (err) {
        if (cancelled) return;
        setLogs([]);
        setTotalCount(0);
        setError(err instanceof Error ? err.message : "Failed to load API logs.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    loadLogs();

    return () => {
      cancelled = true;
    };
  }, [search, statusFilter, currentPage]);

  const totalPages = Math.max(1, Math.ceil(totalCount / itemsPerPage));

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const formatTimestamp = (value: string) => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  };

  const exportLogs = async () => {
    try {
      const result = await getAdminLogs({
        search: search.trim() || undefined,
        status: statusFilter === "All" ? undefined : Number(statusFilter),
        page: 1,
        page_size: 100,
      });

      const header = [
        "Timestamp",
        "API Key",
        "Method",
        "Endpoint",
        "Response Time (ms)",
        "Status",
        "IP Address",
      ];

      const rows = result.items.map((log) => [
        formatTimestamp(log.created_at),
        log.api_key_name || (log.is_anonymous ? "Anonymous" : "—"),
        log.method,
        log.path + (log.query_string ? `?${log.query_string}` : ""),
        String(log.duration_ms),
        String(log.status_code),
        log.ip_address || "—",
      ]);

      const csv = [header, ...rows]
        .map((row) =>
          row
            .map((value) => `"${String(value).replace(/"/g, '""')}"`)
            .join(",")
        )
        .join("\n");

      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `api-logs-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to export API logs.");
    }
  };

  return (
    <div>
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold">API Logs</h2>
          <p className="text-slate-500 mt-1">
            Monitor real API usage, requests and response performance.
          </p>
        </div>
        <button
          type="button"
          onClick={exportLogs}
          className="px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
        >
          Export CSV
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5 mb-6">
        <LogStatCard title="Total Requests" value={totalCount.toLocaleString()} icon="↗" />
        <LogStatCard title="Successful" value={stats.successful.toLocaleString()} icon="✓" />
        <LogStatCard title="Rate Limited" value={stats.rateLimited.toLocaleString()} icon="⚠" />
        <LogStatCard title="Avg Response" value={`${stats.averageResponse} ms`} icon="⚡" />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Search Logs
            </label>
            <input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search by API key or endpoint..."
              className="w-full border border-slate-300 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full border border-slate-300 rounded-lg px-4 py-3 bg-white"
            >
              <option value="All">All Statuses</option>
              <option value="200">200 Success</option>
              <option value="400">400 Bad Request</option>
              <option value="401">401 Unauthorized</option>
              <option value="403">403 Forbidden</option>
              <option value="404">404 Not Found</option>
              <option value="429">429 Rate Limited</option>
              <option value="500">500 Server Error</option>
            </select>
          </div>
        </div>

        {(search || statusFilter !== "All") && (
          <div className="mt-4 flex items-center justify-between gap-3">
            <p className="text-sm text-slate-500">
              {totalCount.toLocaleString()} matching requests
            </p>
            <button
              type="button"
              onClick={() => {
                setSearch("");
                setStatusFilter("All");
                setCurrentPage(1);
              }}
              className="text-sm text-blue-600 hover:underline"
            >
              Clear Filters
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="p-6 border-b">
          <h3 className="font-semibold">Recent API Requests</h3>
          <p className="text-sm text-slate-500 mt-1">
            Live request activity from the backend.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[950px]">
            <thead className="bg-slate-50">
              <tr>
                <th className="text-left px-5 py-4 text-sm font-semibold">Timestamp</th>
                <th className="text-left px-5 py-4 text-sm font-semibold">API Key</th>
                <th className="text-left px-5 py-4 text-sm font-semibold">Method</th>
                <th className="text-left px-5 py-4 text-sm font-semibold">Endpoint</th>
                <th className="text-left px-5 py-4 text-sm font-semibold">Response</th>
                <th className="text-left px-5 py-4 text-sm font-semibold">Status</th>
                <th className="text-left px-5 py-4 text-sm font-semibold">IP Address</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                    Loading API logs...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                    No API logs found.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="border-t hover:bg-slate-50">
                    <td className="px-5 py-4 text-sm whitespace-nowrap">
                      {formatTimestamp(log.created_at)}
                    </td>
                    <td className="px-5 py-4 text-sm font-medium">
                      {log.api_key_name || (log.is_anonymous ? "Anonymous" : "—")}
                    </td>
                    <td className="px-5 py-4">
                      <span className="font-mono text-xs bg-slate-100 px-2 py-1 rounded">
                        {log.method}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="font-mono text-sm bg-slate-100 px-2 py-1 rounded">
                        {log.path}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className={log.duration_ms > 300 ? "text-orange-600 font-medium" : "text-slate-700"}>
                        {log.duration_ms} ms
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                          log.status_code >= 200 && log.status_code < 300
                            ? "bg-green-50 text-green-700"
                            : log.status_code === 429
                            ? "bg-red-50 text-red-700"
                            : "bg-amber-50 text-amber-700"
                        }`}
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-current" />
                        {log.status_code}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600">
                      {log.ip_address || "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="px-5 py-4 border-t flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-slate-500">
            {totalCount === 0
              ? "Showing 0 requests"
              : `Showing ${(currentPage - 1) * itemsPerPage + 1}–${Math.min(
                  currentPage * itemsPerPage,
                  totalCount
                )} of ${totalCount.toLocaleString()}`}
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={currentPage <= 1 || loading}
              onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
              className="px-3 py-2 border rounded-lg text-sm disabled:opacity-40"
            >
              ← Previous
            </button>
            <span className="text-sm text-slate-600 px-2">
              Page {currentPage} of {totalPages}
            </span>
            <button
              type="button"
              disabled={currentPage >= totalPages || loading}
              onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
              className="px-3 py-2 border rounded-lg text-sm disabled:opacity-40"
            >
              Next →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function LogStatCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon: string;
}) {

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">

      <div className="flex items-center justify-between">

        <div>

          <p className="text-sm text-slate-500">
            {title}
          </p>

          <p className="text-2xl font-bold text-slate-900 mt-2">
            {value}
          </p>

        </div>


        <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center">
          {icon}
        </div>

      </div>

    </div>
  );
}


/* =========================
   SETTINGS
========================= */

function SettingsPage({ onNotify }: { onNotify?: (title: string, message: string, type?: NotificationType) => void }) {
  const apiBaseUrl = API_BASE_URL;
  const productionProxy = import.meta.env.PROD;

  const detectedEnvironment = (() => {
    const value = apiBaseUrl.toLowerCase();

    if (value.includes("localhost") || value.includes("127.0.0.1")) {
      return "Development";
    }

    if (value.includes("staging") || value.includes("stage")) {
      return "Staging";
    }

    return "Production";
  })();

  const [notifications, setNotifications] = useState(() => {
    try {
      const saved = localStorage.getItem("village_api_notification_settings");
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (error) {
      console.error("Failed to load notification settings:", error);
    }

    return {
      usageAlerts: true,
      securityAlerts: true,
    };
  });

  const [savedMessage, setSavedMessage] = useState("");

  const updateNotification = (key: string) => {
    setNotifications((current: Record<string, boolean>) => ({
      ...current,
      [key]: !current[key],
    }));
    setSavedMessage("");
  };

  const saveSettings = () => {
    try {
      localStorage.setItem(
        "village_api_notification_settings",
        JSON.stringify(notifications)
      );
      setSavedMessage("Settings saved successfully.");
      onNotify?.("Settings saved", "Notification preferences were saved successfully.", "success");
    } catch (error) {
      console.error("Failed to save settings:", error);
      setSavedMessage("Unable to save settings.");
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-3xl font-bold">
          Settings
        </h2>
        <p className="text-slate-500 mt-1">
          Platform configuration
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">
                API Configuration
              </h3>
              <p className="text-sm text-slate-500 mt-1">
                Connection details used by the admin platform
              </p>
            </div>

            <span className="inline-flex items-center rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
              Connected
            </span>
          </div>

          <div className="space-y-5">
            <div>
              <label className="text-sm font-medium text-slate-700">
                API Base URL
              </label>
              <input
                value={apiBaseUrl}
                readOnly
                className="w-full border border-slate-300 rounded-lg px-4 py-3 mt-2 bg-slate-50 text-slate-700 outline-none"
              />
              <p className="text-xs text-slate-500 mt-2">
                {productionProxy
                  ? "Production requests use a secure server-side proxy; API credentials are not exposed in the browser."
                  : "This value is provided by the local frontend environment configuration."}
              </p>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700">
                Environment
              </label>
              <div className="w-full border border-slate-300 rounded-lg px-4 py-3 mt-2 bg-slate-50 text-slate-700 flex items-center justify-between">
                <span>{detectedEnvironment}</span>
                <span className="text-xs font-medium text-slate-500">
                  Auto-detected
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="mb-5">
            <h3 className="text-lg font-semibold text-slate-900">
              Notifications
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              Choose which admin notifications you want to receive
            </p>
          </div>

          <div className="space-y-4">
            <label className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-4 hover:bg-slate-50 transition cursor-pointer">
              <div>
                <p className="font-medium text-slate-800">
                  Usage alerts
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Alerts when API usage approaches limits
                </p>
              </div>
              <input
                type="checkbox"
                checked={notifications.usageAlerts}
                onChange={() => updateNotification("usageAlerts")}
                className="h-4 w-4 accent-blue-600"
              />
            </label>

            <label className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-4 hover:bg-slate-50 transition cursor-pointer">
              <div>
                <p className="font-medium text-slate-800">
                  Security alerts
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Important authentication and security events
                </p>
              </div>
              <input
                type="checkbox"
                checked={notifications.securityAlerts}
                onChange={() => updateNotification("securityAlerts")}
                className="h-4 w-4 accent-blue-600"
              />
            </label>

          </div>

          <div className="mt-6 flex items-center justify-between gap-4">
            <p className="text-sm text-emerald-600 min-h-[20px]">
              {savedMessage}
            </p>
            <button
              type="button"
              onClick={saveSettings}
              className="px-5 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition shadow-sm"
            >
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}


export default App;