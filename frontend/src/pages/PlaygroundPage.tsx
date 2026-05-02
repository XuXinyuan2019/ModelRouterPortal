import { useState, useRef, useEffect, useCallback } from "react";
import {
  Card,
  Input,
  Select,
  Button,
  Typography,
  Space,
  message,
  Alert,
} from "antd";

const { TextArea } = Input;
const { Title, Text } = Typography;

import {
  SendOutlined,
  DeleteOutlined,
  LoadingOutlined,
  StopOutlined,
} from "@ant-design/icons";
import { listActivatedModels, type ActivationInfo } from "../api/models";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  reasoning?: string;
}

const PROXY_URL = "/api/v1/chat/completions";

export default function PlaygroundPage() {
  const [modelId, setModelId] = useState("");
  const [activatedModels, setActivatedModels] = useState<ActivationInfo[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load activated models
  useEffect(() => {
    setModelsLoading(true);
    listActivatedModels()
      .then((models) => {
        setActivatedModels(models);
        if (models.length > 0 && !modelId) {
          setModelId(models[0].model_id);
        }
      })
      .catch(() => message.error("加载已开通模型失败"))
      .finally(() => setModelsLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleStop = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setLoading(false);
  }, []);

  const handleSend = useCallback(async () => {
    const content = inputValue.trim();
    if (!content) return;

    if (!modelId) {
      message.warning("请先选择一个模型 / Please select a model");
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      message.error("未登录 / Not logged in");
      return;
    }

    const userMessage: ChatMessage = { role: "user", content };
    const conversationHistory = [
      ...messages,
      userMessage,
    ].map(({ role, content: c }) => ({ role, content: c }));

    setMessages((prev) => [...prev, userMessage, { role: "assistant", content: "" }]);
    setInputValue("");
    setLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch(PROXY_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          model: modelId,
          messages: conversationHistory,
          stream: true,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorDetail = `HTTP ${response.status}`;
        try {
          const errBody = await response.text();
          errorDetail += `: ${errBody}`;
        } catch {
          // ignore
        }
        if (response.status === 401) {
          message.error("登录已过期，请重新登录");
        } else if (response.status === 402) {
          message.error("余额不足，请先充值 / Insufficient balance");
        } else if (response.status === 403) {
          message.error("模型未开通 / Model not activated");
        } else {
          message.error(`请求失败 - ${errorDetail}`);
        }
        setMessages((prev) => prev.slice(0, -1));
        setLoading(false);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        message.error("无法读取响应流");
        setMessages((prev) => prev.slice(0, -1));
        setLoading(false);
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith("data: ")) continue;
          const data = trimmed.slice(6);
          if (data === "[DONE]") break;

          try {
            const parsed = JSON.parse(data);
            if (parsed.error) {
              message.error(`错误: ${parsed.error}`);
              break;
            }
            const delta = parsed.choices?.[0]?.delta;
            if (delta) {
              const contentDelta = delta.content || "";
              const reasoningDelta = delta.reasoning_content || "";
              if (contentDelta || reasoningDelta) {
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last && last.role === "assistant") {
                    updated[updated.length - 1] = {
                      ...last,
                      content: last.content + contentDelta,
                      reasoning: (last.reasoning || "") + reasoningDelta,
                    };
                  }
                  return updated;
                });
              }
            }
          } catch {
            // skip malformed JSON
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        // user cancelled
      } else {
        message.error("网络错误，请检查后重试 / Network error");
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === "assistant" && !last.content) {
            return prev.slice(0, -1);
          }
          return prev;
        });
      }
    } finally {
      abortControllerRef.current = null;
      setLoading(false);
    }
  }, [inputValue, messages, modelId]);

  const handleClear = useCallback(() => {
    if (loading) {
      handleStop();
    }
    setMessages([]);
  }, [loading, handleStop]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (!loading) {
          handleSend();
        }
      }
    },
    [loading, handleSend]
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0, marginBottom: 12 }}>
          Chat Playground
        </Title>
        <Card size="small" styles={{ body: { padding: "12px 16px" } }}>
          <Space>
            <Text type="secondary" style={{ fontSize: 12 }}>模型</Text>
            <Select
              size="small"
              style={{ minWidth: 200 }}
              value={modelId || undefined}
              onChange={setModelId}
              placeholder="选择已开通的模型"
              loading={modelsLoading}
              options={activatedModels.map((m) => ({
                value: m.model_id,
                label: m.model_id,
              }))}
            />
          </Space>
          {activatedModels.length === 0 && !modelsLoading && (
            <Alert
              type="info"
              showIcon
              message="暂无已开通模型，请先在模型市场开通 / No activated models, please activate one first"
              style={{ marginTop: 8 }}
            />
          )}
        </Card>
      </div>

      {/* Chat area */}
      <div
        style={{
          flex: 1,
          minHeight: 0,
          height: "calc(100vh - 360px)",
          overflowY: "auto",
          padding: "16px 0",
          borderTop: "1px solid #f0f0f0",
          borderBottom: "1px solid #f0f0f0",
        }}
      >
        {messages.length === 0 ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              color: "#bfbfbf",
            }}
          >
            <Text type="secondary" style={{ fontSize: 16 }}>
              输入消息开始对话 / Type a message to start
            </Text>
          </div>
        ) : (
          <div style={{ padding: "0 8px" }}>
            {messages.map((msg, index) => (
              <div
                key={index}
                style={{
                  display: "flex",
                  justifyContent:
                    msg.role === "user" ? "flex-end" : "flex-start",
                  marginBottom: 12,
                }}
              >
                <div
                  style={{
                    maxWidth: "70%",
                    padding: "10px 16px",
                    borderRadius: 12,
                    backgroundColor:
                      msg.role === "user" ? "#1677ff" : "#f0f0f0",
                    color: msg.role === "user" ? "#fff" : "#000",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    lineHeight: 1.6,
                  }}
                >
                  {msg.role === "assistant" && msg.reasoning && (
                    <details style={{ marginBottom: 8, fontSize: 12, color: "#888" }}>
                      <summary style={{ cursor: "pointer", userSelect: "none" }}>
                        思考过程
                      </summary>
                      <div style={{
                        marginTop: 4,
                        padding: "8px",
                        background: "#e8e8e8",
                        borderRadius: 6,
                        whiteSpace: "pre-wrap",
                        wordBreak: "break-word",
                        maxHeight: 200,
                        overflowY: "auto",
                      }}>
                        {msg.reasoning}
                      </div>
                    </details>
                  )}
                  {msg.content}
                  {msg.role === "assistant" &&
                    !msg.content && !msg.reasoning &&
                    loading &&
                    index === messages.length - 1 && (
                      <LoadingOutlined style={{ color: "#999" }} />
                    )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div style={{ paddingTop: 12 }}>
        <Space.Compact style={{ width: "100%" }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息，Enter 发送，Shift+Enter 换行"
            autoSize={{ minRows: 1, maxRows: 4 }}
            style={{ borderTopRightRadius: 0, borderBottomRightRadius: 0 }}
            disabled={loading || !modelId}
          />
          {loading ? (
            <Button
              type="default"
              danger
              icon={<StopOutlined />}
              onClick={handleStop}
              style={{ height: "auto" }}
            />
          ) : (
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={!inputValue.trim() || !modelId}
              style={{ height: "auto" }}
            />
          )}
          <Button
            icon={<DeleteOutlined />}
            onClick={handleClear}
            disabled={messages.length === 0 && !loading}
            style={{ height: "auto" }}
          />
        </Space.Compact>
      </div>
    </div>
  );
}
