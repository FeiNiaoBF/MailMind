"""

"""
from datetime import tzinfo, timedelta
from pytz import timezone  # 需要安装 pytz 包：pip install pytz

# 定义中国时区（UTC+8）
china_tz = timezone('Asia/Shanghai')

# 兼容性处理（如果不想用 pytz）
class ChinaTimezone(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=8)
    def tzname(self, dt):
        return "UTC+08:00"
    def dst(self, dt):
        return timedelta(0)

china_tz = ChinaTimezone()  # 或直接使用 pytz 的 timezone('Asia/Shanghai')
