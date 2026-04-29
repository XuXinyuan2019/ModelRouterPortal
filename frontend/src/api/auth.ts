import client from "./client";
import type { TokenResponse, UserInfo } from "../types";

export async function register(
  username: string,
  password: string,
  display_name?: string
): Promise<TokenResponse> {
  const { data } = await client.post<TokenResponse>("/auth/register", {
    username,
    password,
    display_name,
  });
  return data;
}

export async function login(
  username: string,
  password: string
): Promise<TokenResponse> {
  const { data } = await client.post<TokenResponse>("/auth/login", {
    username,
    password,
  });
  return data;
}

export async function getMe(): Promise<UserInfo> {
  const { data } = await client.get<UserInfo>("/auth/me");
  return data;
}
