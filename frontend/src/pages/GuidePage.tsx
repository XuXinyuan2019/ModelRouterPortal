import { useEffect, useState } from "react";
import {
  Typography,
  Card,
  Tabs,
  Table,
  Collapse,
  Button,
  Tag,
  Space,
  Divider,
} from "antd";
import {
  CodeOutlined,
  RocketOutlined,
  QuestionCircleOutlined,
  BookOutlined,
  LoginOutlined,
} from "@ant-design/icons";
import { Link } from "react-router-dom";
import { listModels, type ModelInfo } from "../api/models";

const { Title, Paragraph, Text } = Typography;

const BASE_URL = "https://model-router.edu-aliyun.com";

const pythonCode = `from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="${BASE_URL}/v1",
)

completion = client.chat.completions.create(
    model="qwen3.6-plus",
    messages=[
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
)
print(completion.choices[0].message.content)`;

const curlCode = `curl -X POST ${BASE_URL}/v1/chat/completions \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "qwen3.6-plus",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
  }'`;

const jsCode = `const response = await fetch(
  "${BASE_URL}/v1/chat/completions",
  {
    method: "POST",
    headers: {
      "Authorization": "Bearer YOUR_API_KEY",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "qwen3.6-plus",
      messages: [
        { role: "user", content: "你好，请介绍一下你自己" }
      ],
    }),
  }
);
const data = await response.json();
console.log(data.choices[0].message.content);`;

const faqItems = [
  {
    key: "1",
    label: "如何获取 API Key？",
    children:
      "注册并登录后，进入「API Key」管理页面，点击「创建 Key」按钮即可生成。请妥善保管，Key 仅在创建时展示一次。",
  },
  {
    key: "2",
    label: "支持哪些模型？",
    children:
      "当前平台支持 Qwen3.6-Plus、Qwen3-Max、Kimi-K2.6、DeepSeek-V4-Pro 等模型。您需要在「模型市场」中自助开通后才能使用。",
  },
  {
    key: "3",
    label: "API 调用的 Base URL 是什么？",
    children: `所有模型的 API 调用都通过阿里云 ModelRouter 端点：${BASE_URL}/v1。认证方式为 Bearer Token（即您的 API Key）。详细文档请参阅：https://model-router-console.edu-aliyun.com/manual`,
  },
  {
    key: "4",
    label: "如何计费？",
    children:
      "各模型按 token 用量计费，具体价格请在模型详情页查看计费规则。您可以在「用量统计」页面查看消费明细。",
  },
  {
    key: "5",
    label: "新注册用户能直接调用模型吗？",
    children:
      "不能。新用户注册后需要在「模型市场」页面自助开通需要使用的模型，开通后即可调用。",
  },
];

const modelColumns = [
  { title: "模型名称", dataIndex: "name", key: "name" },
  { title: "Model ID", dataIndex: "model_id", key: "model_id", render: (v: string) => <Text code>{v}</Text> },
  { title: "类型", dataIndex: "model_type", key: "model_type", render: (v: string) => <Tag color="blue">{v}</Tag> },
  { title: "供应商", dataIndex: "provider", key: "provider" },
];

export default function GuidePage() {
  const [models, setModels] = useState<ModelInfo[]>([]);

  useEffect(() => {
    listModels().then(setModels).catch(() => {});
  }, []);

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: "48px 24px" }}>
      <div style={{ textAlign: "center", marginBottom: 48 }}>
        <Title level={1}>ModelRouter Portal</Title>
        <Paragraph style={{ fontSize: 18, color: "#666" }}>
          一站式 AI 模型接入平台 — 浏览模型、自助开通、获取 API Key、即刻调用
        </Paragraph>
        <Space size="middle" style={{ marginTop: 16 }}>
          <Link to="/register">
            <Button type="primary" size="large" icon={<RocketOutlined />}>
              立即注册
            </Button>
          </Link>
          <Link to="/login">
            <Button size="large" icon={<LoginOutlined />}>
              登录
            </Button>
          </Link>
        </Space>
      </div>

      <Divider />

      {/* 快速开始 */}
      <Card
        title={
          <span>
            <BookOutlined style={{ marginRight: 8 }} />
            快速开始
          </span>
        }
        style={{ marginBottom: 24 }}
      >
        <Paragraph>
          <Text strong>1.</Text> 注册账号并登录本平台
        </Paragraph>
        <Paragraph>
          <Text strong>2.</Text> 在「模型市场」中浏览并开通所需模型
        </Paragraph>
        <Paragraph>
          <Text strong>3.</Text> 在「API Key」页面创建密钥
        </Paragraph>
        <Paragraph>
          <Text strong>4.</Text> 使用以下地址和密钥调用 API：
        </Paragraph>
        <Card size="small" style={{ background: "#f6f8fa" }}>
          <Paragraph style={{ margin: 0 }}>
            <Text strong>Base URL: </Text>
            <Text code copyable>
              {BASE_URL}/v1
            </Text>
          </Paragraph>
          <Paragraph style={{ margin: "8px 0 0" }}>
            <Text strong>认证方式: </Text>
            <Text code>Authorization: Bearer YOUR_API_KEY</Text>
          </Paragraph>
        </Card>
      </Card>

      {/* 代码示例 */}
      <Card
        title={
          <span>
            <CodeOutlined style={{ marginRight: 8 }} />
            代码示例
          </span>
        }
        style={{ marginBottom: 24 }}
      >
        <Tabs
          items={[
            {
              key: "python",
              label: "Python",
              children: <pre style={{ background: "#f6f8fa", padding: 16, borderRadius: 8, overflow: "auto", fontSize: 13 }}>{pythonCode}</pre>,
            },
            {
              key: "curl",
              label: "cURL",
              children: <pre style={{ background: "#f6f8fa", padding: 16, borderRadius: 8, overflow: "auto", fontSize: 13 }}>{curlCode}</pre>,
            },
            {
              key: "js",
              label: "JavaScript",
              children: <pre style={{ background: "#f6f8fa", padding: 16, borderRadius: 8, overflow: "auto", fontSize: 13 }}>{jsCode}</pre>,
            },
          ]}
        />
      </Card>

      {/* 可用模型 */}
      <Card title="可用模型列表" style={{ marginBottom: 24 }}>
        <Table
          columns={modelColumns}
          dataSource={models}
          rowKey="model_id"
          pagination={false}
          size="middle"
        />
      </Card>

      {/* FAQ */}
      <Card
        title={
          <span>
            <QuestionCircleOutlined style={{ marginRight: 8 }} />
            常见问题
          </span>
        }
      >
        <Collapse items={faqItems} bordered={false} />
      </Card>
    </div>
  );
}
