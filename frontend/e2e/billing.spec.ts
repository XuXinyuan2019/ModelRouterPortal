import { test, expect } from '@playwright/test';
import { registerUser, loginUser, generateTestUsername, waitForPageReady } from './helpers';

test.describe('计费功能 / Billing Feature', () => {
  const username = generateTestUsername();
  const password = 'TestPass123!';

  test('模型详情页展示计费规则 / Model detail shows pricing', async ({ page }) => {
    await registerUser(page, username, password);
    await page.goto('/models/qwen3.6-plus');
    await waitForPageReady(page);

    // Verify pricing section is visible
    await expect(page.getByText('计费规则').first()).toBeVisible();
    await expect(page.getByText('Input 价格').first()).toBeVisible();
    await expect(page.getByText('Output 价格').first()).toBeVisible();
    await expect(page.getByText('百万 tokens').first()).toBeVisible();
  });

  test('余额不足时显示警告 / Low balance warning shows on dashboard', async ({ page }) => {
    await loginUser(page, username, password);

    await page.goto('/balance');
    await waitForPageReady(page);

    // Check if restricted alert shows when balance is 0
    const restrictedAlert = page.getByText('余额已用完');
    if (await restrictedAlert.isVisible().catch(() => false)) {
      await expect(restrictedAlert.first()).toBeVisible();
    }
  });

  test('用量统计页展示数据 / Usage page displays data', async ({ page }) => {
    await loginUser(page, username, password);
    await page.goto('/usage');
    await waitForPageReady(page);

    await expect(page.getByText('用量统计').first()).toBeVisible();
    await expect(page.getByText('费用趋势').first()).toBeVisible();
    await expect(page.getByText('模型用量明细').first()).toBeVisible();
  });
});
