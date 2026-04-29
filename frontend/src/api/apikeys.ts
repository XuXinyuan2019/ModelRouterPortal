import client from "./client";

export interface ApiKeyCreated {
  id: number | null;
  api_key: string;
  status: string;
  created_at: string;
}

export interface ApiKeyItem {
  id: number | null;
  api_key_preview: string;
  status: string;
  created_at: string | null;
}

export async function createApiKey(): Promise<ApiKeyCreated> {
  const { data } = await client.post<ApiKeyCreated>("/api-keys/");
  return data;
}

export async function listApiKeys(): Promise<ApiKeyItem[]> {
  const { data } = await client.get<ApiKeyItem[]>("/api-keys/");
  return data;
}

export async function deleteApiKey(keyId: number): Promise<void> {
  await client.delete(`/api-keys/${keyId}`);
}
