import { useEffect, useState } from "react";
import {
  Typography,
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Spin,
  message,
} from "antd";
import { BarChartOutlined } from "@ant-design/icons";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import {
  getUsageOverview,
  getUsageTrend,
  getModelUsage,
  type UsageOverview,
  type UsageTrendItem,
  type ModelUsageItem,
} from "../api/usage";

const { Title, Text } = Typography;

export default function UsagePage() {
  const [overview, setOverview] = useState<UsageOverview | null>(null);
  const [trend, setTrend] = useState<UsageTrendItem[]>([]);
  const [modelUsage, setModelUsage] = useState<ModelUsageItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getUsageOverview(), getUsageTrend(7), getModelUsage()])
      .then(([o, t, m]) => {
        setOverview(o);
        setTrend(t);
        setModelUsage(m);
      })
      .catch(() => message.error("加载用量数据失败"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  const modelColumns = [
    { title: "模型", dataIndex: "model_name", key: "model_name" },
    {
      title: "Model ID",
      dataIndex: "model_id",
      key: "model_id",
      render: (v: string) => <Text code>{v}</Text>,
    },
    {
      title: "费用",
      dataIndex: "cost",
      key: "cost",
      sorter: (a: ModelUsageItem, b: ModelUsageItem) => a.cost - b.cost,
      render: (v: number) => `¥ ${v.toFixed(2)}`,
    },
    {
      title: "Token 数",
      dataIndex: "tokens",
      key: "tokens",
      sorter: (a: ModelUsageItem, b: ModelUsageItem) => a.tokens - b.tokens,
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: "请求数",
      dataIndex: "requests",
      key: "requests",
      sorter: (a: ModelUsageItem, b: ModelUsageItem) =>
        a.requests - b.requests,
      render: (v: number) => v.toLocaleString(),
    },
  ];

  return (
    <div>
      <Title level={3}>
        <BarChartOutlined style={{ marginRight: 8 }} />
        用量统计
      </Title>

      {overview && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={8}>
            <Card>
              <Statistic
                title={`${overview.period} 总费用`}
                value={overview.total_cost}
                precision={2}
                prefix="¥"
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card>
              <Statistic
                title="总 Token 数"
                value={overview.total_tokens}
                formatter={(v) => Number(v).toLocaleString()}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card>
              <Statistic
                title="总请求数"
                value={overview.total_requests}
                formatter={(v) => Number(v).toLocaleString()}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="费用趋势 (近7日)">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(v: string) => v.slice(5)}
                />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => [
                    `¥ ${value.toFixed(2)}`,
                    "费用",
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="cost"
                  stroke="#1677ff"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="请求趋势 (近7日)">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(v: string) => v.slice(5)}
                />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => [
                    value.toLocaleString(),
                    "请求数",
                  ]}
                />
                <Bar dataKey="requests" fill="#52c41a" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Card title="模型用量明细">
        <Table
          columns={modelColumns}
          dataSource={modelUsage}
          rowKey="model_id"
          pagination={false}
        />
      </Card>
    </div>
  );
}
