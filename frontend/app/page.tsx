"use client";

import { Button } from "@heroui/button";
import { Card } from "@heroui/card";
import { Link } from "@heroui/link";

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-12 space-y-12">
      <div className="text-center space-y-6">
        <h1 className="text-6xl font-bold tracking-tight sm:text-8xl bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">
          MailMind
        </h1>
        <p className="text-2xl text-muted-foreground max-w-3xl mx-auto">
          使用AI处理邮件
        </p>
        <div className="flex gap-4 justify-center">
          <Button
            as={Link}
            href="/chat"
            color="primary"
            variant="solid"
            size="lg"
            className="text-lg px-8 py-6"
          >
            开始使用
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        <Card className="p-8 h-full hover:shadow-lg transition-shadow">
          <h3 className="text-2xl font-semibold mb-4 text-primary">智能分类</h3>
          <p className="text-lg text-muted-foreground">
            自动对邮件进行分类和优先级排序，让重要信息一目了然
          </p>
        </Card>

        <Card className="p-8 h-full hover:shadow-lg transition-shadow">
          <h3 className="text-2xl font-semibold mb-4 text-primary">快速回复</h3>
          <p className="text-lg text-muted-foreground">
            AI 辅助生成专业的邮件回复，提高工作效率
          </p>
        </Card>

        <Card className="p-8 h-full hover:shadow-lg transition-shadow">
          <h3 className="text-2xl font-semibold mb-4 text-primary">邮件摘要</h3>
          <p className="text-lg text-muted-foreground">
            自动生成邮件内容摘要，节省阅读时间，快速把握重点
          </p>
        </Card>
      </div>
    </div>
  );
}
