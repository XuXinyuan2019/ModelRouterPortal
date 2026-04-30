import { useEffect, useState } from "react";
import {
  Typography,
  Button,
  Table,
  Modal,
  message,
  Alert,
  Space,
  Popconfirm,
  Input,
  Card,
} from "antd";
import {
  PlusOutlined,
  DeleteOutlined,
  CopyOutlined,
  KeyOutlined,
  ExclamationCircleFilled,
} from "@ant-design/icons";
import {
  createApiKey,
  listApiKeys,
  copyApiKey,
  deleteApiKey,
  type ApiKeyItem,
} from "../api/apikeys";

const { Title, Text, Paragraph } = Typography;

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [createLoading, setCreateLoading] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);

  const fetchKeys = () => {
    setLoading(true);
    listApiKeys()
      .then(setKeys)
      .catch(() => message.error("加载 API Key 列表失败"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreate = async () => {
    setCreateLoading(true);
    try {
      const result = await createApiKey();
      setNewKey(result.api_key);
      fetchKeys();
    } catch (err: any) {
      message.error(err.response?.data?.detail || "创建失败");
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDelete = async (keyId: number) => {
    try {
      await deleteApiKey(keyId);
      message.success("已删除");
      fetchKeys();
    } catch (err: any) {
      message.error(err.response?.data?.detail || "删除失败");
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success("已复制到剪贴板");
    });
  };

  const handleCopyPreview = async (record: ApiKeyItem) => {
    if (record.id === null) return;
    try {
      const result = await copyApiKey(record.id);
      if (result.api_key) {
        navigator.clipboard.writeText(result.api_key).then(() => {
          message.success("完整 API Key 已复制到剪贴板");
        });
      } else {
        message.warning("未能获取完整 API Key");
      }
    } catch (err: any) {
      message.error(err.response?.data?.detail || "复制失败");
    }
  };

  const columns = [
    {
      title: "API Key",
      dataIndex: "api_key_preview",
      key: "api_key_preview",
      render: (v: string) => <Text code>{v}</Text>,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 100,
      render: (v: string) => (
        <Text type={v === "active" ? "success" : "secondary"}>{v === "active" ? "有效" : v}</Text>
      ),
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 200,
      render: (v: string | null) => v ? new Date(v).toLocaleString("zh-CN") : "-",
    },
    {
      title: "操作",
      key: "action",
      width: 100,
      render: (_: unknown, record: ApiKeyItem) => (
        <Space>
          <Button
            type="link"
            icon={<CopyOutlined />}
            size="small"
            onClick={() => handleCopyPreview(record)}
          >
            复制
          </Button>
          <Popconfirm
            title="确定删除此 API Key?"
            description="删除后将无法恢复，使用该 Key 的调用将立即失效。"
            onConfirm={() => record.id !== null && handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button type="link" danger icon={<DeleteOutlined />} size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 24,
        }}
      >
        <Title level={3} style={{ margin: 0 }}>
          <KeyOutlined style={{ marginRight: 8 }} />
          API Key 管理
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          loading={createLoading}
        >
          创建 Key
        </Button>
      </div>

      <Card size="small" style={{ marginBottom: 16, background: "#f6f8fa" }}>
        <Paragraph style={{ margin: 0 }} type="secondary">
          创建 API Key 后，使用该 Key 直接调用阿里云 ModelRouter 端点。Base URL:{" "}
          <Text code>https://aicontent.cn-beijing.aliyuncs.com/compatible-mode/v1</Text>
        </Paragraph>
      </Card>

      <Table
        columns={columns}
        dataSource={keys}
        rowKey="id"
        loading={loading}
        pagination={false}
        locale={{ emptyText: "暂无 API Key，点击「创建 Key」生成" }}
      />

      {/* New Key Modal — show only once on creation */}
      <Modal
        title={
          <Space>
            <ExclamationCircleFilled style={{ color: "#faad14" }} />
            API Key 已创建
          </Space>
        }
        open={newKey !== null}
        onOk={() => setNewKey(null)}
        onCancel={() => setNewKey(null)}
        okText="我已保存"
        cancelButtonProps={{ style: { display: "none" } }}
        closable={false}
        maskClosable={false}
      >
        <Alert
          message="请立即复制并妥善保存此 Key，关闭后将无法再次查看完整内容。"
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Input.TextArea
          value={newKey || ""}
          readOnly
          autoSize={{ minRows: 2 }}
          style={{ fontFamily: "monospace", marginBottom: 12 }}
        />
        <Button
          icon={<CopyOutlined />}
          onClick={() => newKey && handleCopy(newKey)}
          block
        >
          复制 Key
        </Button>
      </Modal>
    </div>
  );
}
