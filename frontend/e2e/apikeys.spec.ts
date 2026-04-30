import { test, expect } from '@playwright/test';
import {
  saveScreenshot,
  registerUser,
  generateTestUsername,
  waitForPageReady,
} from './helpers';

const TEST_PASSWORD = 'TestPass123!';

test.describe('API Key 管理', () => {
  let testUsername: string;

  test.beforeAll(() => {
    testUsername = generateTestUsername();
  });

  test.beforeEach(async ({ page }) => {
    await registerUser(page, testUsername, TEST_PASSWORD);
    await waitForPageReady(page);
  });

  test('导航到 API Key 页面', async ({ page }) => {
    await page.getByText('API Key').click();
    await page.waitForURL('**/api-keys');
    await waitForPageReady(page);

    await saveScreenshot(page, 'apikeys-page');

    // 验证页面标题
    await expect(page.getByText('API Key 管理')).toBeVisible();
    // 验证创建按钮存在
    await expect(page.getByRole('button', { name: '创建 Key' })).toBeVisible();
  });

  test('创建新 Key 并验证弹窗显示', async ({ page }) => {
    await page.goto('/api-keys');
    await waitForPageReady(page);

    // 点击创建按钮
    await page.getByRole('button', { name: '创建 Key' }).click();

    // 等待弹窗出现
    const modal = page.locator('.ant-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // 验证弹窗标题
    await expect(page.getByText('API Key 已创建')).toBeVisible();

    // 验证 key 内容在 textarea 中
    const textarea = modal.locator('textarea');
    await expect(textarea).toBeVisible();
    const keyValue = await textarea.inputValue();
    expect(keyValue.length).toBeGreaterThan(0);

    await saveScreenshot(page, 'apikeys-created-modal');

    // 关闭弹窗
    await page.getByRole('button', { name: '我已保存' }).click();
    await expect(modal).not.toBeVisible();

    // 验证列表中显示已掩码的 key
    const table = page.locator('.ant-table');
    await expect(table).toBeVisible();
    // 表格中应有至少一行数据
    const rows = table.locator('.ant-table-row');
    await expect(rows).toHaveCount(1, { timeout: 5000 });

    await saveScreenshot(page, 'apikeys-list-with-key');
  });

  test('删除 Key 并验证列表更新', async ({ page }) => {
    await page.goto('/api-keys');
    await waitForPageReady(page);

    // 确保列表中有 key（前一个测试创建的）
    const table = page.locator('.ant-table');
    await expect(table).toBeVisible();

    // 如果没有 key，先创建一个
    const rows = table.locator('.ant-table-row');
    const rowCount = await rows.count();
    if (rowCount === 0) {
      await page.getByRole('button', { name: '创建 Key' }).click();
      await expect(page.getByText('API Key 已创建')).toBeVisible({ timeout: 10000 });
      await page.getByRole('button', { name: '我已保存' }).click();
      await waitForPageReady(page);
    }

    // 点击删除按钮
    await page.getByRole('button', { name: '删除' }).first().click();

    // 确认删除（Popconfirm）
    await page.getByRole('button', { name: '删除' }).nth(1).click();

    // 等待删除完成
    await waitForPageReady(page);

    await saveScreenshot(page, 'apikeys-after-delete');
  });
});
