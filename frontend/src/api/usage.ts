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
  input_tokens: number;
  output_tokens: number;
}

export interface ModelDetailRow {
  timestamp: string;
  total_calls: number;
  all_tokens: number;
  input_tokens: number;
  output_tokens: number;
  reasoning_tokens: number;
  total_amount: number;
}

export interface ModelDetailData {
  rows: ModelDetailRow[];
  total: number;
  page: number;
  page_size: number;
  model_id: number | null;
  model_name: string | null;
  granularity: string;
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

export async function getModelDetailUsage(
  modelId: number,
  days = 30
): Promise<ModelDetailData> {
  const { data } = await client.get<ModelDetailData>(
    `/usage/models/${modelId}`,
    { params: { days } }
  );
  return data;
}

export async function getDashboard(): Promise<DashboardData> {
  const { data } = await client.get<DashboardData>("/dashboard/");
  return data;
}
