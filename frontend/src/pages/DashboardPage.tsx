import { Typography } from "antd";

export default function DashboardPage() {
  return (
    <div>
      <Typography.Title level={3}>控制台</Typography.Title>
      <Typography.Paragraph>
        欢迎使用 ModelRouter Portal，这里将展示余额、消费和调用概览。
      </Typography.Paragraph>
    </div>
  );
}
