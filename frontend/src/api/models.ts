import client from "./client";

export interface ModelInfo {
  id: number;
  model_id: string;
  name: string;
  description: string | null;
  model_type: string;
  provider: string;
  icon_url: string | null;
  is_available: boolean;
  sort_order: number;
}

export interface ModelDetail extends ModelInfo {
  activated: boolean;
  billing_rules: { input: number; output: number } | null;
}

export interface ActivationInfo {
  id: number;
  user_id: number;
  model_id: string;
  status: string;
  activated_at: string;
  deactivated_at: string | null;
}

export async function listModels(): Promise<ModelInfo[]> {
  const { data } = await client.get<ModelInfo[]>("/models/");
  return data;
}

export async function getModelDetail(modelId: string): Promise<ModelDetail> {
  const { data } = await client.get<ModelDetail>(`/models/${modelId}`);
  return data;
}

export async function activateModel(modelId: string): Promise<ActivationInfo> {
  const { data } = await client.post<ActivationInfo>(
    `/models/${modelId}/activate`
  );
  return data;
}

export async function deactivateModel(
  modelId: string
): Promise<ActivationInfo> {
  const { data } = await client.post<ActivationInfo>(
    `/models/${modelId}/deactivate`
  );
  return data;
}

export async function listActivatedModels(): Promise<ActivationInfo[]> {
  const { data } = await client.get<ActivationInfo[]>("/models/activated");
  return data;
}
