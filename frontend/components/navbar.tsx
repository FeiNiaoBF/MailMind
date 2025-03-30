"use client";

import {
  Navbar as HeroUINavbar,
  NavbarContent,
  NavbarMenu,
  NavbarMenuToggle,
  NavbarBrand,
  NavbarItem,
  NavbarMenuItem,
} from "@heroui/navbar";
import { Button } from "@heroui/button";
import { Link } from "@heroui/link";
import { link as linkStyles } from "@heroui/theme";
import NextLink from "next/link";
import clsx from "clsx";

import { siteConfig } from "@/config/site";
import { ThemeSwitch } from "@/components/theme-switch";
import { GithubIcon } from "@/components/icons";
import React from "react";

/**
 * 用户导航组件
 *
 * 显示在应用程序顶部的用户导航菜单
 * 根据认证状态显示不同的选项
 * 包括主题切换、语言切换和用户菜单
 */

export const Navbar = () => {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <HeroUINavbar
      onMenuOpenChange={setIsOpen}
      maxWidth="xl"
      position="sticky"
      className="border-b border-divider"
    >
      <NavbarContent className="basis-1/5 sm:basis-full" justify="start">
        <NavbarBrand as="li" className="gap-3 max-w-fit">
          <NextLink className="flex justify-start items-center gap-1" href="/">
            <p className="font-bold text-inherit">MailMind</p>
          </NextLink>
        </NavbarBrand>
        <ul className="hidden lg:flex gap-4 justify-start ml-2">
          {siteConfig.navItems.map((item) => (
            <NavbarItem key={item.href}>
              <NextLink
                className={clsx(
                  linkStyles({ color: "foreground" }),
                  "data-[active=true]:text-primary data-[active=true]:font-medium transition-colors duration-200 hover:text-primary",
                )}
                color="foreground"
                href={item.href}
              >
                {item.label}
              </NextLink>
            </NavbarItem>
          ))}
        </ul>
      </NavbarContent>

      <NavbarContent
        className="hidden sm:flex basis-1/5 sm:basis-full"
        justify="end"
      >
        <NavbarItem className="hidden sm:flex gap-2">
          <Link
            isExternal
            aria-label="Github"
            href={siteConfig.links.github}
            className="hover:opacity-80 transition-opacity"
          >
            <GithubIcon className="text-default-500" />
          </Link>
          <ThemeSwitch />
        </NavbarItem>

        <NavbarItem className="hidden md:flex">
          <Button
            as={Link}
            className="text-sm font-medium"
            color="primary"
            variant="flat"
            href="/login"
          >
            登录
          </Button>
        </NavbarItem>
      </NavbarContent>

      <NavbarContent className="sm:hidden basis-1 pl-4" justify="end">
        <Link
          isExternal
          aria-label="Github"
          href={siteConfig.links.github}
          className="hover:opacity-80 transition-opacity"
        >
          <GithubIcon className="text-default-500" />
        </Link>
        <ThemeSwitch />
        <NavbarMenuToggle
          aria-label={isOpen ? "Close menu" : "Open menu"}
          className="sm:hidden"
        />
        <NavbarMenu>
          {siteConfig.navItems.map((item) => (
            <NavbarMenuItem key={item.href}>
              <Link
                className="flex items-center gap-1"
                color="foreground"
                href={item.href}
              >
                {item.label}
              </Link>
            </NavbarMenuItem>
          ))}
        </NavbarMenu>
      </NavbarContent>
    </HeroUINavbar>
  );
};
