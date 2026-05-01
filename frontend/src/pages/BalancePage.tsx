import { useEffect, useState } from "react";
import {
  Typography,
  Card,
  Button,
  Table,
  Modal,
  Form,
  InputNumber,
  Input,
  Tag,
  Statistic,
  message,
  Space,
  Spin,
  Alert,
} from "antd";
import { WalletOutlined, PlusOutlined } from "@ant-design/icons";
import {
  getBalance,
  getBalanceStatus,
  submitRecharge,
  getRechargeHistory,
  type BalanceInfo,
  type BalanceStatus,
  type RechargeRecord,
} from "../api/balance";

const { Title } = Typography;

const statusMap: Record<string, { color: string; label: string }> = {
  pending: { color: "orange", label: "待审批" },
  completed: { color: "green", label: "已完成" },
  failed: { color: "red", label: "已拒绝" },
};

export default function BalancePage() {
  const [balance, setBalance] = useState<BalanceInfo | null>(null);
  const [status, setStatus] = useState<BalanceStatus | null>(null);
  const [records, setRecords] = useState<RechargeRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [b, s, r] = await Promise.all([
        getBalance(),
        getBalanceStatus(),
        getRechargeHistory(),
      ]);
      setBalance(b);
      setStatus(s);
      setRecords(r);
    } catch {
      message.error("加载数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmit = async (values: { amount: number; remark?: string }) => {
    setSubmitLoading(true);
    try {
      await submitRecharge(values.amount, values.remark);
      message.success("充值成功");
      setModalOpen(false);
      form.resetFields();
      fetchData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || "提交失败");
    } finally {
      setSubmitLoading(false);
    }
  };

  const columns = [
    {
      title: "金额",
      dataIndex: "amount",
      key: "amount",
      render: (v: number) => `¥ ${v.toFixed(2)}`,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (v: string) => {
        const s = statusMap[v] || { color: "default", label: v };
        return <Tag color={s.color}>{s.label}</Tag>;
      },
    },
    {
      title: "充值前余额",
      dataIndex: "balance_before",
      key: "balance_before",
      render: (v: number) => `¥ ${v.toFixed(2)}`,
    },
    {
      title: "充值后余额",
      dataIndex: "balance_after",
      key: "balance_after",
      render: (v: number) => `¥ ${v.toFixed(2)}`,
    },
    {
      title: "备注",
      dataIndex: "remark",
      key: "remark",
      render: (v: string | null) => v || "-",
    },
    {
      title: "申请时间",
      dataIndex: "created_at",
      key: "created_at",
      render: (v: string) => new Date(v).toLocaleString("zh-CN"),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

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
          <WalletOutlined style={{ marginRight: 8 }} />
          余额充值
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalOpen(true)}
        >
          模拟充值
        </Button>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <Statistic
          title="当前余额"
          value={balance?.balance ?? 0}
          precision={2}
          prefix="¥"
          valueStyle={{ color: status?.restricted ? "#ff4d4f" : "#1677ff", fontSize: 36 }}
        />
        {status?.restricted && (
          <Alert
            message="账户已受限 / Account Restricted"
            description="余额为 0，API Key 已被禁用。请充值以恢复使用。"
            type="error"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Card>

      <Card title="充值记录">
        <Table
          columns={columns}
          dataSource={records}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: "暂无充值记录" }}
        />
      </Card>

      <Modal
        title="模拟充值"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleSubmit} layout="vertical">
          <Form.Item
            name="amount"
            label="充值金额"
            rules={[{ required: true, message: "请输入充值金额" }]}
          >
            <InputNumber
              min={1}
              max={100000}
              precision={2}
              prefix="¥"
              style={{ width: "100%" }}
              placeholder="请输入充值金额"
            />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} placeholder="可选备注" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={submitLoading}
              >
                确认充值
              </Button>
              <Button onClick={() => setModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
