import { useState } from "react";
import { Typography, Card, Form, Input, Button, message } from "antd";
import { SettingOutlined, LockOutlined } from "@ant-design/icons";
import { changePassword } from "../api/settings";

const { Title } = Typography;

export default function SettingsPage() {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleSubmit = async (values: {
    old_password: string;
    new_password: string;
  }) => {
    setLoading(true);
    try {
      await changePassword(values.old_password, values.new_password);
      message.success("密码修改成功");
      form.resetFields();
    } catch (err: any) {
      message.error(err.response?.data?.detail || "修改失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={3}>
        <SettingOutlined style={{ marginRight: 8 }} />
        账户设置
      </Title>

      <Card title="修改密码" style={{ maxWidth: 500 }}>
        <Form form={form} onFinish={handleSubmit} layout="vertical">
          <Form.Item
            name="old_password"
            label="当前密码"
            rules={[{ required: true, message: "请输入当前密码" }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="输入当前密码"
            />
          </Form.Item>
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: "请输入新密码" },
              { min: 6, message: "密码至少6个字符" },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="输入新密码"
            />
          </Form.Item>
          <Form.Item
            name="confirm"
            label="确认新密码"
            dependencies={["new_password"]}
            rules={[
              { required: true, message: "请确认新密码" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("new_password") === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("两次输入的密码不一致"));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="再次输入新密码"
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
