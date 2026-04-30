import { test, expect } from '@playwright/test';
import {
  saveScreenshot,
  registerUser,
  generateTestUsername,
  waitForPageReady,
} from './helpers';

const TEST_PASSWORD = 'TestPass123!';

test.describe('模型市场流程', () => {
  let testUsername: string;

  test.beforeAll(() => {
    testUsername = generateTestUsername();
  });

  test.beforeEach(async ({ page }) => {
    // 注册并登录
    await registerUser(page, testUsername, TEST_PASSWORD);
    await waitForPageReady(page);
  });

  test('导航到模型市场页面并查看模型卡片', async ({ page }) => {
    // 通过侧边栏导航到模型市场
    await page.getByText('模型市场').click();
    await page.waitForURL('**/models');
    await waitForPageReady(page);

    await saveScreenshot(page, 'models-market');

    // 验证模型市场标题
    await expect(page.getByRole('heading', { name: '模型市场' })).toBeVisible();

    // 验证至少有 4 个模型卡片
    const cards = page.locator('.ant-card');
    await expect(cards).toHaveCount(4, { timeout: 10000 });
  });

  test('点击模型卡片进入详情页', async ({ page }) => {
    await page.goto('/models');
    await waitForPageReady(page);

    // 点击第一个模型卡片
    const firstCard = page.locator('.ant-card').first();
    await firstCard.click();

    // 等待导航到详情页
    await page.waitForURL('**/models/*');
    await waitForPageReady(page);

    await saveScreenshot(page, 'models-detail');

    // 验证详情页内容
    await expect(page.getByText('返回模型市场')).toBeVisible();
    await expect(page.getByText('Model ID')).toBeVisible();
    await expect(page.getByText('接入代码示例')).toBeVisible();
  });

  test('激活模型并验证状态变化', async ({ page }) => {
    await page.goto('/models');
    await waitForPageReady(page);

    // 点击第一个模型卡片进入详情
    const firstCard = page.locator('.ant-card').first();
    await firstCard.click();
    await page.waitForURL('**/models/*');
    await waitForPageReady(page);

    // 点击"开通模型"按钮
    const activateButton = page.getByRole('button', { name: '开通模型' });
    await expect(activateButton).toBeVisible();
    await activateButton.click();

    // 等待操作完成，验证状态变为"已开通"
    await expect(page.getByText('已开通')).toBeVisible({ timeout: 10000 });

    await saveScreenshot(page, 'models-activated');

    // 验证出现"关闭"按钮（表示已激活）
    await expect(page.getByRole('button', { name: '关闭' })).toBeVisible();
  });

  test('返回模型市场验证激活标签显示', async ({ page }) => {
    await page.goto('/models');
    await waitForPageReady(page);

    // 验证模型市场中有"已开通"标签
    await expect(page.getByText('已开通').first()).toBeVisible({ timeout: 10000 });

    await saveScreenshot(page, 'models-market-with-activation');
  });
});
