import client from "./client";

export async function changePassword(
  oldPassword: string,
  newPassword: string
): Promise<void> {
  await client.put("/settings/password", {
    old_password: oldPassword,
    new_password: newPassword,
  });
}
