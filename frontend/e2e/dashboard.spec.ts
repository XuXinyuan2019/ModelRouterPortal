import { test, expect } from '@playwright/test';
import {
  saveScreenshot,
  registerUser,
  generateTestUsername,
  waitForPageReady,
  expectURL,
} from './helpers';

const TEST_PASSWORD = 'TestPass123!';

test.describe('仪表板', () => {
  let testUsername: string;

  test.beforeAll(() => {
    testUsername = generateTestUsername();
  });

  test.beforeEach(async ({ page }) => {
    await registerUser(page, testUsername, TEST_PASSWORD);
    await waitForPageReady(page);
  });

  test('Dashboard 页面展示关键指标卡片', async ({ page }) => {
    // 注册后自动在 Dashboard
    await expectURL(page, '/dashboard');

    await saveScreenshot(page, 'dashboard-page');

    // 验证控制台标题
    await expect(page.getByRole('heading', { name: '控制台' })).toBeVisible();

    // 验证 4 个指标卡片存在
    await expect(page.getByText('当前余额')).toBeVisible();
    await expect(page.getByText('近7日消费')).toBeVisible();
    await expect(page.getByText('近7日调用')).toBeVisible();
    await expect(page.getByText('已开通模型')).toBeVisible();
  });

  test('验证趋势图表区域存在', async ({ page }) => {
    await page.goto('/dashboard');
    await waitForPageReady(page);

    // 验证图表卡片标题
    await expect(page.getByText('近7日费用趋势')).toBeVisible();

    // 验证 Recharts 容器存在
    const chartContainer = page.locator('.recharts-responsive-container');
    await expect(chartContainer).toBeVisible({ timeout: 10000 });

    await saveScreenshot(page, 'dashboard-chart');
  });

  test('点击余额卡片导航到余额页面', async ({ page }) => {
    await page.goto('/dashboard');
    await waitForPageReady(page);

    // 点击"当前余额"卡片
    const balanceCard = page.locator('.ant-card').filter({ hasText: '当前余额' });
    await balanceCard.click();

    // 验证跳转到余额页面
    await page.waitForURL('**/balance', { timeout: 5000 });
    await expectURL(page, '/balance');

    await saveScreenshot(page, 'dashboard-navigate-to-balance');
  });

  test('点击已开通模型卡片导航到模型市场', async ({ page }) => {
    await page.goto('/dashboard');
    await waitForPageReady(page);

    // 点击"已开通模型"卡片
    const modelsCard = page.locator('.ant-card').filter({ hasText: '已开通模型' });
    await modelsCard.click();

    // 验证跳转到模型市场
    await page.waitForURL('**/models', { timeout: 5000 });
    await expectURL(page, '/models');

    await saveScreenshot(page, 'dashboard-navigate-to-models');
  });
});
