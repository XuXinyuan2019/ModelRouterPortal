import { useEffect, useState } from "react";
import { Card, Tag, Input, Typography, Row, Col, Spin, message } from "antd";
import { SearchOutlined, CheckCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { listModels, listActivatedModels, type ModelInfo, type ActivationInfo } from "../api/models";

const { Title, Paragraph, Text } = Typography;

const providerColors: Record<string, string> = {
  "通义": "blue",
  "月之暗面": "purple",
  "DeepSeek": "green",
};

export default function ModelMarketPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [activations, setActivations] = useState<ActivationInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([listModels(), listActivatedModels()])
      .then(([m, a]) => {
        setModels(m);
        setActivations(a);
      })
      .catch(() => message.error("加载模型列表失败"))
      .finally(() => setLoading(false));
  }, []);

  const activatedIds = new Set(activations.map((a) => a.model_id));

  const filtered = models.filter(
    (m) =>
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.model_id.toLowerCase().includes(search.toLowerCase()) ||
      m.provider.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          模型市场
        </Title>
        <Input
          placeholder="搜索模型名称、ID 或供应商"
          prefix={<SearchOutlined />}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 300 }}
          allowClear
        />
      </div>

      <Row gutter={[16, 16]}>
        {filtered.map((model) => {
          const isActivated = activatedIds.has(model.model_id);
          return (
            <Col xs={24} sm={12} lg={8} key={model.model_id}>
              <Card
                hoverable
                onClick={() => navigate(`/models/${model.model_id}`)}
                style={{ height: "100%" }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                  <Title level={5} style={{ margin: 0 }}>
                    {model.name}
                  </Title>
                  {isActivated && (
                    <Tag icon={<CheckCircleOutlined />} color="success">
                      已开通
                    </Tag>
                  )}
                </div>
                <Paragraph
                  type="secondary"
                  ellipsis={{ rows: 2 }}
                  style={{ marginBottom: 12 }}
                >
                  {model.description || "暂无描述"}
                </Paragraph>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <Tag color={providerColors[model.provider] || "default"}>
                      {model.provider}
                    </Tag>
                    <Tag>{model.model_type}</Tag>
                  </div>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    <Text code style={{ fontSize: 12 }}>{model.model_id}</Text>
                  </Text>
                </div>
              </Card>
            </Col>
          );
        })}
      </Row>
    </div>
  );
}
