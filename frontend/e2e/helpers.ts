import { Page, expect } from '@playwright/test';
import path from 'path';

// 截图保存目录
const SCREENSHOTS_DIR = path.resolve(__dirname, '../../test-artifacts/screenshots');

/**
 * 保存截图到 test-artifacts/screenshots/ 目录
 * @param page Playwright Page 对象
 * @param name 截图文件名（不含扩展名）
 */
export async function saveScreenshot(page: Page, name: string): Promise<string> {
  const filePath = path.join(SCREENSHOTS_DIR, `${name}.png`);
  await page.screenshot({ path: filePath, fullPage: true });
  return filePath;
}

/**
 * 注册新用户
 * @param page Playwright Page 对象
 * @param username 用户名
 * @param password 密码
 * @param displayName 显示名称（可选）
 */
export async function registerUser(
  page: Page,
  username: string,
  password: string,
  displayName?: string
): Promise<void> {
  await page.goto('/register');
  await page.waitForLoadState('networkidle');

  // 填写用户名
  await page.getByPlaceholder('用户名').fill(username);

  // 填写显示名称（可选）
  if (displayName) {
    await page.getByPlaceholder('显示名称（可选）').fill(displayName);
  }

  // 填写密码
  await page.getByPlaceholder('密码', { exact: true }).fill(password);

  // 填写确认密码
  await page.getByPlaceholder('确认密码').fill(password);

  // 点击注册按钮
  await page.getByRole('button', { name: '注册' }).click();

  // 等待导航到 dashboard
  await page.waitForURL('**/dashboard', { timeout: 10000 });
}

/**
 * 登录用户
 * @param page Playwright Page 对象
 * @param username 用户名
 * @param password 密码
 */
export async function loginUser(
  page: Page,
  username: string,
  password: string
): Promise<void> {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  // 填写用户名
  await page.getByPlaceholder('用户名').fill(username);

  // 填写密码
  await page.getByPlaceholder('密码').fill(password);

  // 点击登录按钮
  await page.getByRole('button', { name: '登录' }).click();

  // 等待导航到 dashboard
  await page.waitForURL('**/dashboard', { timeout: 10000 });
}

/**
 * 退出登录
 * @param page Playwright Page 对象
 */
export async function logoutUser(page: Page): Promise<void> {
  // 点击右上角用户头像打开下拉菜单
  await page.locator('.ant-dropdown-trigger').click();
  // 点击退出登录
  await page.getByText('退出登录').click();
  // 等待跳转到登录页
  await page.waitForURL('**/login', { timeout: 5000 });
}

/**
 * 等待页面加载完成（包含 API 请求）
 * @param page Playwright Page 对象
 */
export async function waitForPageReady(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle');
}

/**
 * 断言页面标题/文本存在
 * @param page Playwright Page 对象
 * @param text 期望的文本
 */
export async function expectTextVisible(page: Page, text: string): Promise<void> {
  await expect(page.getByText(text).first()).toBeVisible({ timeout: 5000 });
}

/**
 * 断言当前 URL 匹配
 * @param page Playwright Page 对象
 * @param urlPattern URL 模式
 */
export async function expectURL(page: Page, urlPattern: string): Promise<void> {
  await expect(page).toHaveURL(new RegExp(urlPattern), { timeout: 5000 });
}

/**
 * 生成唯一的测试用户名（避免冲突）
 */
export function generateTestUsername(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 6);
  return `test_${timestamp}_${random}`;
}
