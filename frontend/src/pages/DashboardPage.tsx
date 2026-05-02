import { useEffect, useState } from "react";
import { Card, Col, Row, Statistic, Typography, Spin, Alert } from "antd";
import {
  WalletOutlined,
  ThunderboltOutlined,
  AppstoreOutlined,
  DollarOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { getDashboard, type DashboardData } from "../api/usage";

const { Title } = Typography;

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getDashboard()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div>
      <Title level={3}>控制台</Title>

      {data.balance <= 0 && (
        <Alert
          message="余额已用完 / Balance Depleted"
          description="您的余额为 0，API Key 已被限制使用。请先充值。"
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {data.balance > 0 && data.balance < 10 && (
        <Alert
          message="余额不足 / Low Balance"
          description="您的余额低于 10 元，请及时充值以避免服务中断。"
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => navigate("/balance")}>
            <Statistic
              title="当前余额"
              value={data.balance}
              precision={2}
              prefix={<WalletOutlined style={{ color: "#1677ff" }} />}
              suffix="元"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => navigate("/usage")}>
            <Statistic
              title="近7日消费"
              value={data.total_cost_30d}
              precision={2}
              prefix={<DollarOutlined style={{ color: "#fa8c16" }} />}
              suffix="元"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => navigate("/usage")}>
            <Statistic
              title="近7日调用"
              value={data.total_requests_30d}
              prefix={<ThunderboltOutlined style={{ color: "#52c41a" }} />}
              suffix="次"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => navigate("/models")}>
            <Statistic
              title="已开通模型"
              value={data.activated_models}
              prefix={<AppstoreOutlined style={{ color: "#722ed1" }} />}
              suffix="个"
            />
          </Card>
        </Col>
      </Row>

      <Card title="近7日费用趋势">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.recent_trend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tickFormatter={(v: string) => v.slice(5)}
            />
            <YAxis />
            <Tooltip
              formatter={(value) => [`¥ ${Number(value).toFixed(2)}`, "费用"]}
              labelFormatter={(label) => `日期: ${String(label)}`}
            />
            <Line
              type="monotone"
              dataKey="cost"
              stroke="#1677ff"
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
