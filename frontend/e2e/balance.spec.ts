import { test, expect } from '@playwright/test';
import {
  saveScreenshot,
  registerUser,
  generateTestUsername,
  waitForPageReady,
} from './helpers';

const TEST_PASSWORD = 'TestPass123!';

test.describe('余额充值', () => {
  let testUsername: string;

  test.beforeAll(() => {
    testUsername = generateTestUsername();
  });

  test.beforeEach(async ({ page }) => {
    await registerUser(page, testUsername, TEST_PASSWORD);
    await waitForPageReady(page);
  });

  test('导航到余额页面并验证初始余额', async ({ page }) => {
    await page.getByText('余额充值').click();
    await page.waitForURL('**/balance');
    await waitForPageReady(page);

    await saveScreenshot(page, 'balance-page');

    // 验证页面标题
    await expect(page.getByRole('heading', { name: /余额充值/ })).toBeVisible();

    // 验证余额卡片存在（显示"当前余额"标题）
    await expect(page.getByText('当前余额')).toBeVisible();

    // 验证模拟充值按钮
    await expect(page.getByRole('button', { name: '模拟充值' })).toBeVisible();

    // 验证充值记录表格
    await expect(page.getByText('充值记录')).toBeVisible();
  });

  test('提交充值申请并验证历史记录', async ({ page }) => {
    await page.goto('/balance');
    await waitForPageReady(page);

    // 点击充值按钮
    await page.getByRole('button', { name: '模拟充值' }).click();

    // 等待弹窗出现
    const modal = page.locator('.ant-modal');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // 验证弹窗标题
    await expect(page.getByText('模拟充值').nth(1)).toBeVisible();

    // 填写充值金额
    const amountInput = modal.locator('.ant-input-number-input');
    await amountInput.fill('100');

    // 填写备注（可选）
    await modal.getByPlaceholder('可选备注').fill('E2E 测试充值');

    // 提交
    await page.getByRole('button', { name: '提交充值申请' }).click();

    // 等待弹窗关闭
    await expect(modal).not.toBeVisible({ timeout: 10000 });
    await waitForPageReady(page);

    await saveScreenshot(page, 'balance-after-recharge');

    // 验证充值历史中出现新记录（状态为待审批）
    await expect(page.getByText('待审批')).toBeVisible({ timeout: 10000 });
  });
});
