export type SiteConfig = typeof siteConfig;

export const siteConfig = {
  name: "MailMind AI邮件",
  description: "使用AI分析邮件内容",
  navItems: [
    // {
    //   label: "主页",
    //   href: "/",
    // },
    {
      label: "AI对话",
      href: "/chat",
    },
    {
      label: "邮件箱",
      href: "/index",
    },
    {
      label: "设置",
      href: "/setting",
    },
  ],
  navMenuItems: [
    {
      label: "Profile",
      href: "/profile",
    },
    {
      label: "Dashboard",
      href: "/dashboard",
    },
    {
      label: "Logout",
      href: "/logout",
    },
  ],
  // TODO: 加入自己的链接
  links: {
    github: "https://github.com/",
  },
};
