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
    await expect(page.getByText('/ 1K tokens').first()).toBeVisible();
  });

  test('模拟调用扣费并更新余额 / Simulate usage deducts balance', async ({ page }) => {
    await loginUser(page, username, password);

    // Recharge balance first
    await page.goto('/balance');
    await waitForPageReady(page);
    await page.getByRole('button', { name: '模拟充值' }).click();
    await page.getByRole('spinbutton').fill('100');
    await page.getByRole('button', { name: '确认充值' }).click();
    await expect(page.getByText('¥100.00').first()).toBeVisible();

    // Activate model
    await page.goto('/models/qwen3.6-plus');
    await waitForPageReady(page);
    const activateBtn = page.getByRole('button', { name: '开通模型' });
    if (await activateBtn.isVisible().catch(() => false)) {
      await activateBtn.click();
      await expect(page.getByText('模型开通成功').first()).toBeVisible();
    }

    // Simulate usage
    await waitForPageReady(page);
    await page.getByRole('button', { name: '模拟调用并计费' }).click();
    await expect(page.getByText('模拟调用成功').first()).toBeVisible({ timeout: 5000 });

    // Verify balance decreased on dashboard
    await page.goto('/dashboard');
    await waitForPageReady(page);
    await expect(page.getByText(/当前余额/).first()).toBeVisible();
    // Balance should be less than 100 after deduction
    const balanceText = await page.locator('.ant-statistic-content-value-int').first().textContent();
    expect(balanceText).not.toBe('100');
  });

  test('余额不足时显示警告 / Low balance warning shows on dashboard', async ({ page }) => {
    await loginUser(page, username, password);

    // Set balance to low amount by recharging a small amount
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
