export interface UserInfo {
  id: number;
  username: string;
  display_name: string | null;
  client_id: number | null;
  is_active: boolean;
  is_admin: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
