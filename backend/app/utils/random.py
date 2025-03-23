"""
为测试做 random 的工具
"""

import random


def random_string(length: int) -> str:
    """生成随机字符串
    :param length: 字符串长度
    :return: 随机字符串
    """
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=length))


def random_number(length: int) -> str:
    """生成随机数字
    :param length: 数字长度
    :return: 随机数字
    """
    return ''.join(random.choices('0123456789', k=length))


def random_email() -> str:
    """生成随机邮箱地址
    :return: 随机邮箱地址
    """
    return f"test_{random_string(8)}@{random_string(5)}.com"
