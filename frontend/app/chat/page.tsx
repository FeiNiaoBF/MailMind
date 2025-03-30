"use client";

// 用于显示AI聊天的页面
import { Card } from "@heroui/card";

import { ChatSection } from "@/components/chat";

export default function ChatPage() {
  return (
    <div className="flex-1 flex items-start pt-6">
      <div className="w-full max-w-4xl mx-auto">
        <Card className="w-full h-[calc(100vh-14rem)]">
          <ChatSection />
        </Card>
      </div>
    </div>
  );
}
