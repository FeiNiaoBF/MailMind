// 用于chat的组件
"use client";

import React, { useState, useRef, useEffect } from "react";
import { Button } from "@heroui/button";
import { Card, CardHeader, CardBody, CardFooter } from "@heroui/card";
import { Input } from "@heroui/input";
import { Avatar } from "@heroui/avatar";

interface Message {
  id: number;
  content: string;
  isUser: boolean;
  timestamp: string;
}

export function ChatSection() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // 当消息列表更新时，自动滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 模拟AI回复
  const generateAIResponse = async (userMessage: string) => {
    setIsLoading(true);
    // 模拟API调用延迟
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      id: messages.length + 2,
      content: `已收到您的请求："${userMessage}"，正在处理中...`,
      isUser: false,
      timestamp: new Date().toLocaleTimeString("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    // 添加用户消息
    const userMessage: Message = {
      id: messages.length + 1,
      content: inputMessage,
      isUser: true,
      timestamp: new Date().toLocaleTimeString("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");

    try {
      // 获取AI回复
      const aiResponse = await generateAIResponse(inputMessage);
      setMessages((prev) => [...prev, aiResponse]);
    } catch (error) {
      console.error("AI回复生成失败:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* 初始欢迎消息 */}
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground py-4">
            <p className="text-lg font-medium">欢迎使用MailMind AI助手</p>
          </div>
        )}

        {/* 消息列表 */}
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] flex gap-3 ${message.isUser ? "flex-row-reverse" : ""}`}
            >
              <Avatar
                name={message.isUser ? "Me" : "AI"}
                size="sm"
                className="flex-none"
              />
              <div
                className={`p-3 rounded-xl ${
                  message.isUser
                    ? "bg-primary text-primary-foreground"
                    : "bg-default-100"
                }`}
              >
                <p className="text-sm break-words">{message.content}</p>
                <div className="text-xs opacity-75 mt-1">
                  {message.timestamp}
                </div>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区 */}
      <div className="border-t border-divider p-4">
        <div className="flex gap-2">
          <Input
            placeholder="请输入您的问题..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
            disabled={isLoading}
            className="flex-1"
          />
          <Button
            color="primary"
            onPress={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-6"
          >
            {isLoading ? "发送中..." : "发送"}
          </Button>
        </div>
      </div>
    </div>
  );
}
