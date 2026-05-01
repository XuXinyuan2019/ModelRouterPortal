import client from "./client";

export interface UsageOverview {
  total_cost: number;
  total_tokens: number;
  total_requests: number;
  period: string;
}

export interface UsageTrendItem {
  date: string;
  cost: number;
  tokens: number;
  requests: number;
}

export interface ModelUsageItem {
  model_id: string;
  model_name: string;
  cost: number;
  tokens: number;
  requests: number;
}

export interface DashboardData {
  balance: number;
  total_cost_30d: number;
  total_requests_30d: number;
  activated_models: number;
  recent_trend: UsageTrendItem[];
}

export async function getUsageOverview(): Promise<UsageOverview> {
  const { data } = await client.get<UsageOverview>("/usage/overview");
  return data;
}

export async function getUsageTrend(days = 7): Promise<UsageTrendItem[]> {
  const { data } = await client.get<UsageTrendItem[]>("/usage/trend", {
    params: { days },
  });
  return data;
}

export async function getModelUsage(): Promise<ModelUsageItem[]> {
  const { data } = await client.get<ModelUsageItem[]>("/usage/models");
  return data;
}

export interface UsageSimulateRequest {
  model_id: string;
  tokens_input: number;
  tokens_output: number;
}

export interface UsageSimulateResponse {
  cost: number;
  new_balance: number;
  usage_record_id: number;
}

export async function simulateUsage(
  req: UsageSimulateRequest
): Promise<UsageSimulateResponse> {
  const { data } = await client.post<UsageSimulateResponse>("/usage/simulate", req);
  return data;
}

export async function getDashboard(): Promise<DashboardData> {
  const { data } = await client.get<DashboardData>("/dashboard/");
  return data;
}
