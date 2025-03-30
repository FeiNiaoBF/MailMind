"use client";

// 用于具体AI对话的布局

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div>
      {children} {/* 实际内容在这里滚动 */}
    </div>
  );
}
