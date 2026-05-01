import client from "./client";

export interface BalanceInfo {
  balance: number;
}

export interface RechargeRecord {
  id: number;
  amount: number;
  balance_before: number;
  balance_after: number;
  status: string;
  remark: string | null;
  created_at: string;
  completed_at: string | null;
}

export async function getBalance(): Promise<BalanceInfo> {
  const { data } = await client.get<BalanceInfo>("/balance/");
  return data;
}

export async function submitRecharge(
  amount: number,
  remark?: string
): Promise<RechargeRecord> {
  const { data } = await client.post<RechargeRecord>("/balance/recharge", {
    amount,
    remark,
  });
  return data;
}

export interface BalanceStatus {
  balance: number;
  restricted: boolean;
}

export async function getBalanceStatus(): Promise<BalanceStatus> {
  const { data } = await client.get<BalanceStatus>("/balance/status");
  return data;
}

export async function getRechargeHistory(): Promise<RechargeRecord[]> {
  const { data } = await client.get<RechargeRecord[]>("/balance/history");
  return data;
}
