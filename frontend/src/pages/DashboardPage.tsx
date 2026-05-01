import { useEffect, useState } from "react";
import { Card, Col, Row, Statistic, Typography, Spin } from "antd";
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
              formatter={(value: number) => [`¥ ${value.toFixed(2)}`, "费用"]}
              labelFormatter={(label: string) => `日期: ${label}`}
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
