import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Typography,
  Card,
  Button,
  Tag,
  Descriptions,
  Tabs,
  Spin,
  message,
  Space,
  Alert,
  Statistic,
  Row,
  Col,
} from "antd";
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  StopOutlined,
  CodeOutlined,
  DollarOutlined,
} from "@ant-design/icons";
import {
  getModelDetail,
  activateModel,
  deactivateModel,
  type ModelDetail,
} from "../api/models";

const { Title, Text } = Typography;

const BASE_URL = "https://aicontent.cn-beijing.aliyuncs.com";

function getCodeExamples(modelId: string) {
  return {
    python: `from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="${BASE_URL}/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="${modelId}",
    messages=[
        {"role": "user", "content": "你好"}
    ],
)
print(completion.choices[0].message.content)`,
    curl: `curl -X POST ${BASE_URL}/compatible-mode/v1/chat/completions \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "${modelId}",
    "messages": [{"role": "user", "content": "你好"}]
  }'`,
  };
}

export default function ModelDetailPage() {
  const { modelId } = useParams<{ modelId: string }>();
  const navigate = useNavigate();
  const [model, setModel] = useState<ModelDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchDetail = useCallback(() => {
    if (!modelId) return;
    setLoading(true);
    getModelDetail(modelId)
      .then(setModel)
      .catch(() => message.error("加载模型详情失败"))
      .finally(() => setLoading(false));
  }, [modelId]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  const handleActivate = async () => {
    if (!modelId) return;
    setActionLoading(true);
    try {
      await activateModel(modelId);
      message.success("模型开通成功");
      fetchDetail();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      message.error(detail || "开通失败");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeactivate = async () => {
    if (!modelId) return;
    setActionLoading(true);
    try {
      await deactivateModel(modelId);
      message.success("模型已关闭");
      fetchDetail();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      message.error(detail || "关闭失败");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!model) {
    return <Alert type="error" message="模型未找到" showIcon />;
  }

  const codes = getCodeExamples(model.model_id);
  const rules = model.billing_rules;

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        type="link"
        onClick={() => navigate("/models")}
        style={{ padding: 0, marginBottom: 16 }}
      >
        返回模型市场
      </Button>

      <Card>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: 24,
          }}
        >
          <div>
            <Title level={3} style={{ margin: 0 }}>
              {model.name}
            </Title>
            <Text type="secondary">{model.description}</Text>
          </div>
          <Space>
            {model.activated ? (
              <>
                <Tag icon={<CheckCircleOutlined />} color="success" style={{ fontSize: 14, padding: "4px 12px" }}>
                  已开通
                </Tag>
                <Button
                  icon={<StopOutlined />}
                  onClick={handleDeactivate}
                  loading={actionLoading}
                  danger
                >
                  关闭
                </Button>
              </>
            ) : (
              <Button
                type="primary"
                icon={<CheckCircleOutlined />}
                onClick={handleActivate}
                loading={actionLoading}
                size="large"
              >
                开通模型
              </Button>
            )}
          </Space>
        </div>

        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="Model ID">
            <Text code copyable>
              {model.model_id}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="类型">
            <Tag color="blue">{model.model_type}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="供应商">{model.provider}</Descriptions.Item>
          <Descriptions.Item label="状态">
            {model.is_available ? (
              <Tag color="green">可用</Tag>
            ) : (
              <Tag color="red">不可用</Tag>
            )}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {rules && (
        <Card
          title={
            <span>
              <DollarOutlined style={{ marginRight: 8 }} />
              计费规则
            </span>
          }
          style={{ marginTop: 16 }}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Statistic
                title="Input 价格"
                value={rules.input}
                precision={4}
                prefix="¥"
                suffix="/ 百万 tokens"
              />
            </Col>
            <Col xs={24} sm={12}>
              <Statistic
                title="Output 价格"
                value={rules.output}
                precision={4}
                prefix="¥"
                suffix="/ 百万 tokens"
              />
            </Col>
          </Row>
        </Card>
      )}

      <Card
        title={
          <span>
            <CodeOutlined style={{ marginRight: 8 }} />
            接入代码示例
          </span>
        }
        style={{ marginTop: 16 }}
      >
        <Tabs
          items={[
            {
              key: "python",
              label: "Python",
              children: (
                <pre
                  style={{
                    background: "#f6f8fa",
                    padding: 16,
                    borderRadius: 8,
                    overflow: "auto",
                    fontSize: 13,
                  }}
                >
                  {codes.python}
                </pre>
              ),
            },
            {
              key: "curl",
              label: "cURL",
              children: (
                <pre
                  style={{
                    background: "#f6f8fa",
                    padding: 16,
                    borderRadius: 8,
                    overflow: "auto",
                    fontSize: 13,
                  }}
                >
                  {codes.curl}
                </pre>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
}
