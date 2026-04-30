import { test, expect } from '@playwright/test';
import {
  saveScreenshot,
  registerUser,
  loginUser,
  logoutUser,
  generateTestUsername,
  waitForPageReady,
  expectURL,
} from './helpers';

const TEST_PASSWORD = 'TestPass123!';

test.describe('认证流程', () => {
  let testUsername: string;

  test.beforeAll(() => {
    testUsername = generateTestUsername();
  });

  test('访问登录页并截图', async ({ page }) => {
    await page.goto('/login');
    await waitForPageReady(page);

    // 验证登录页元素
    await expect(page.getByPlaceholder('用户名')).toBeVisible();
    await expect(page.getByPlaceholder('密码')).toBeVisible();
    await expect(page.getByRole('button', { name: '登录' })).toBeVisible();

    await saveScreenshot(page, 'auth-login-page');
  });

  test('注册新用户并跳转到 Dashboard', async ({ page }) => {
    await registerUser(page, testUsername, TEST_PASSWORD);

    // 验证跳转到 Dashboard
    await expectURL(page, '/dashboard');
    await waitForPageReady(page);

    // 验证 Dashboard 页面内容
    await expect(page.getByText('控制台')).toBeVisible();

    await saveScreenshot(page, 'auth-dashboard-after-register');
  });

  test('退出登录并验证返回登录页', async ({ page }) => {
    // 先登录
    await loginUser(page, testUsername, TEST_PASSWORD);
    await waitForPageReady(page);

    // 退出登录
    await logoutUser(page);

    // 验证返回登录页
    await expectURL(page, '/login');
    await expect(page.getByRole('button', { name: '登录' })).toBeVisible();

    await saveScreenshot(page, 'auth-after-logout');
  });

  test('用已注册账号重新登录', async ({ page }) => {
    await loginUser(page, testUsername, TEST_PASSWORD);

    // 验证成功跳转 Dashboard
    await expectURL(page, '/dashboard');
    await waitForPageReady(page);
    await expect(page.getByText('控制台')).toBeVisible();

    await saveScreenshot(page, 'auth-relogin-success');
  });

  test('未登录访问受保护页面重定向到登录页', async ({ page }) => {
    // 清除 localStorage 确保未登录状态
    await page.goto('/login');
    await page.evaluate(() => localStorage.clear());

    // 尝试访问受保护页面
    await page.goto('/dashboard');
    await page.waitForURL('**/login', { timeout: 10000 });

    await expectURL(page, '/login');
    await saveScreenshot(page, 'auth-redirect-to-login');
  });
});
