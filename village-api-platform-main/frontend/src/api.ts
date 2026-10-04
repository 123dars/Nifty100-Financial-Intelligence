// src/api.ts

// Production requests go through the Vercel server-side proxy so API
// credentials never need to be embedded in the browser bundle.
export const API_BASE_URL = import.meta.env.PROD
  ? "/api/proxy"
  : import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

function getAccessToken(): string {
  return (
    localStorage.getItem("access_token") ||
    sessionStorage.getItem("access_token") ||
    ""
  );
}

export interface CurrentUser {
  id: number;
  email: string;
  full_name: string;
  is_admin: boolean;
  is_active: boolean;
  status?: string;
  plan?: string;
  business_name?: string | null;
  phone?: string | null;
  created_at?: string;
}

export interface State {
  id: number;
  name: string;
  code?: string;
}

export interface District {
  id: number;
  name: string;
  code?: string;
  state_id?: number;
}

export interface SubDistrict {
  id: number;
  name: string;
  code?: string;
  district_id?: number;
}

export interface Village {
  id?: number;
  name: string;
  code?: string;
  state?: string;
  district?: string;
  sub_district?: string;
  state_name?: string;
  district_name?: string;
  sub_district_name?: string;
}

export interface DashboardStats {
  totalVillages: number;
  activeUsers: number;
  apiRequests: number;
  avgResponseTime: number;
}

export interface ApiRequestTrendItem {
  day: string;
  requests: number;
}

export interface TopStateItem {
  state_name: string;
  state_code: string | number;
  village_count: number;
  district_count: number;
}

export interface AdminLog {
  id: number;
  api_key_name: string | null;
  method: string;
  path: string;
  query_string: string | null;
  status_code: number;
  duration_ms: number;
  ip_address: string | null;
  user_agent: string | null;
  is_anonymous: boolean;
  created_at: string;
}

export interface AdminLogsResponse {
  count: number;
  page: number;
  page_size: number;
  items: AdminLog[];
}

export interface AdminLogsParams {
  api_key_id?: number;
  status?: number;
  search?: string;
  from?: string;
  to?: string;
  page?: number;
  page_size?: number;
}


export interface AdminUserItem {
  id: number;
  email: string;
  full_name: string;
  is_admin: boolean;
  is_active: boolean;
  status: string;
  plan: string;
  business_name?: string | null;
  phone?: string | null;
  gst_number?: string | null;
  admin_notes?: string | null;
  created_at: string;
  last_login_at?: string | null;
  approved_at?: string | null;
  rejected_at?: string | null;
  rejection_reason?: string | null;
}

export interface AdminUsersResponse {
  count: number;
  page: number;
  page_size: number;
  items: AdminUserItem[];
}

export interface UserStateAccessItem {
  id: number;
  code: string | number;
  name: string;
  granted: boolean;
}

export interface UserStateAccess {
  user_id: number;
  has_full_access: boolean;
  granted_state_ids: number[];
  states: UserStateAccessItem[];
}

export interface ApiKeyItem {
  id: number;
  key: string;
  name: string;
  is_active: boolean;
  rate_limit: number;
  total_requests: number;
  created_at: string;
  last_used_at?: string | null;
}

export interface ApiKeyCreatedResponse extends ApiKeyItem {
  secret: string;
}

export interface RotateApiKeyResponse {
  id?: number;
  key?: string;
  api_key?: string;
  secret?: string;
  api_secret?: string;
  name?: string;
  is_active?: boolean;
  rate_limit?: number;
  total_requests?: number;
  created_at?: string;
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const accessToken = getAccessToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",

    ...(accessToken
      ? {
          Authorization: `Bearer ${accessToken}`,
        }
      : {}),

    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  let data: unknown = null;

  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const errorData = data as {
      detail?: string;
      message?: string;
      error?: string;
    };

    throw new Error(
      errorData?.detail ||
        errorData?.message ||
        errorData?.error ||
        `API request failed with status ${response.status}`
    );
  }

  return data as T;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  return apiRequest<CurrentUser>("/auth/me");
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const data = await apiRequest<Record<string, unknown>>(
    "/analytics/summary"
  );

  return {
    totalVillages: Number(
      data.totalVillages ??
        data.total_villages ??
        data.villages ??
        0
    ),
    activeUsers: Number(
      data.activeUsers ??
        data.active_users ??
        data.users ??
        0
    ),
    apiRequests: Number(
      data.apiRequests ??
        data.api_requests ??
        data.total_requests ??
        0
    ),
    avgResponseTime: Number(
      data.avgResponseTime ??
        data.avg_response_time ??
        data.avg_response ??
        data.avg_duration_ms ??
        0
    ),
  };
}

export async function getApiRequestTrend(): Promise<ApiRequestTrendItem[]> {
  const response = await apiRequest<
    ApiRequestTrendItem[] | { data?: ApiRequestTrendItem[] }
  >("/analytics/request-trend");

  const items = Array.isArray(response)
    ? response
    : response.data ?? [];

  return items.map((item) => ({
    day: String(item.day),
    requests: Number(item.requests ?? 0),
  }));
}

export async function getTopStates(): Promise<TopStateItem[]> {
  const response = await apiRequest<
    | TopStateItem[]
    | { top_states?: TopStateItem[]; data?: TopStateItem[] }
  >("/analytics/top-states");

  const items = Array.isArray(response)
    ? response
    : response.top_states ?? response.data ?? [];

  return items.map((item) => ({
    state_name: String(item.state_name ?? ""),
    state_code: item.state_code ?? "",
    village_count: Number(item.village_count ?? 0),
    district_count: Number(item.district_count ?? 0),
  }));
}

export async function getStateAnalytics(
  stateId: number | string
) {
  return apiRequest(`/analytics/state/${stateId}`);
}

export async function getStates(): Promise<State[]> {
  return apiRequest<State[]>("/states");
}

export async function getState(
  stateId: number | string
): Promise<State> {
  return apiRequest<State>(`/states/${stateId}`);
}

export async function getDistricts(
  stateId: number | string
): Promise<District[]> {
  return apiRequest<District[]>(
    `/states/${stateId}/districts`
  );
}

export async function getDistrict(
  districtId: number | string
): Promise<District> {
  return apiRequest<District>(
    `/districts/${districtId}`
  );
}

export async function getSubDistricts(
  districtId: number | string
): Promise<SubDistrict[]> {
  return apiRequest<SubDistrict[]>(
    `/districts/${districtId}/sub-districts`
  );
}

export async function getSubDistrict(
  subDistrictId: number | string
): Promise<SubDistrict> {
  return apiRequest<SubDistrict>(
    `/sub-districts/${subDistrictId}`
  );
}

export async function getVillagesBySubDistrict(
  subDistrictId: number | string
): Promise<Village[]> {
  return apiRequest<Village[]>(
    `/sub-districts/${subDistrictId}/villages`
  );
}

export async function searchVillages(query: string) {
  const params = new URLSearchParams();

  if (query.trim()) {
    params.set("q", query.trim());
  }

  return apiRequest<unknown>(
    `/autocomplete?${params.toString()}`
  );
}

export async function globalSearch(query: string) {
  const params = new URLSearchParams();

  if (query.trim()) {
    params.set("q", query.trim());
  }

  return apiRequest<unknown>(
    `/search?${params.toString()}`
  );
}

export async function generateApiKey(name: string) {
  return apiRequest("/keys/generate", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function getApiKeys() {
  return apiRequest("/keys");
}

export async function rotateApiKey(
  keyId: number | string
): Promise<RotateApiKeyResponse> {
  return apiRequest<RotateApiKeyResponse>(
    `/admin/keys/${keyId}/rotate`,
    { method: "POST" }
  );
}

export async function getAdminLogs(
  params: AdminLogsParams = {}
): Promise<AdminLogsResponse> {
  const query = new URLSearchParams();

  if (params.api_key_id !== undefined) {
    query.set("api_key_id", String(params.api_key_id));
  }

  if (params.status !== undefined) {
    query.set("status", String(params.status));
  }

  if (params.search?.trim()) {
    query.set("search", params.search.trim());
  }

  if (params.from) query.set("from", params.from);
  if (params.to) query.set("to", params.to);

  if (params.page !== undefined) {
    query.set("page", String(params.page));
  }

  if (params.page_size !== undefined) {
    query.set("page_size", String(params.page_size));
  }

  const queryString = query.toString();

  return apiRequest<AdminLogsResponse>(
    `/admin/logs${queryString ? `?${queryString}` : ""}`
  );
}

export async function getAdminUsers(params: {
  search?: string;
  status?: string;
  plan?: string;
  page?: number;
  page_size?: number;
} = {}): Promise<AdminUsersResponse> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.status) query.set("status", params.status);
  if (params.plan) query.set("plan", params.plan);
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  const qs = query.toString();
  return apiRequest<AdminUsersResponse>(`/admin/users${qs ? `?${qs}` : ""}`);
}

export async function updateAdminUser(
  userId: number | string,
  payload: Partial<Pick<AdminUserItem, "is_admin" | "is_active" | "plan" | "status" | "admin_notes">>
): Promise<AdminUserItem> {
  return apiRequest<AdminUserItem>(`/admin/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function approveAdminUser(
  userId: number | string,
  payload: { plan?: string; admin_notes?: string } = {}
): Promise<AdminUserItem> {
  return apiRequest<AdminUserItem>(`/admin/users/${userId}/approve`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function rejectAdminUser(
  userId: number | string,
  payload: { reason: string; admin_notes?: string }
): Promise<AdminUserItem> {
  return apiRequest<AdminUserItem>(`/admin/users/${userId}/reject`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteAdminUser(userId: number | string): Promise<void> {
  await apiRequest<unknown>(`/admin/users/${userId}`, { method: "DELETE" });
}

export async function getUserStateAccess(
  userId: number | string
): Promise<UserStateAccess> {
  return apiRequest<UserStateAccess>(`/admin/users/${userId}/state-access`);
}

export async function updateUserStateAccess(
  userId: number | string,
  payload: { state_ids: number[]; revoke?: boolean }
) {
  return apiRequest(`/admin/users/${userId}/state-access`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createAdminApiKey(
  name: string,
  rate_limit = 1000
): Promise<ApiKeyCreatedResponse> {
  return apiRequest<ApiKeyCreatedResponse>("/admin/keys", {
    method: "POST",
    body: JSON.stringify({ name, rate_limit }),
  });
}

export async function updateAdminApiKey(
  keyId: number | string,
  payload: { is_active?: boolean; rate_limit?: number }
): Promise<ApiKeyItem> {
  return apiRequest<ApiKeyItem>(`/admin/keys/${keyId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function checkApiHealth() {
  const healthUrl = import.meta.env.PROD
    ? `${API_BASE_URL}/health`
    : `${API_BASE_URL.replace(/\/api\/v1\/?$/, "")}/health`;

  const response = await fetch(healthUrl);

  if (!response.ok) {
    throw new Error(
      `Health check failed with status ${response.status}`
    );
  }

  return response.json();
}
