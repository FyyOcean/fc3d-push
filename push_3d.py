import os
import re
import urllib.parse
import urllib.request


def fetch_3d_data():
    """抓取最新试机号数据（以彩之家为例）"""
    url = "https://www.cpzj.com/3d/sjh/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.cpzj.com/",
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # 匹配最新期号、试机号、机球信息（若匹配不到则做兜底）
        issue_match = re.search(r"202\d{4}", html)
        sjh_match = re.search(r'class="[^"]*sjh[^"]*"[^>]*>(\d{3})<', html)
        if not sjh_match:
            # 备选规则：提取表格第一行包含3位数字的单元格
            sjh_match = re.search(r"<td[^>]*>(\d{3})</td>", html)

        issue = issue_match.group(0) if issue_match else "当期"
        sjh = sjh_match.group(1) if sjh_match else "未拉取到"

        # 计算基本形态
        if len(sjh) == 3 and sjh.isdigit():
            b, s, g = int(sjh[0]), int(sjh[1]), int(sjh[2])
            sum_val = b + s + g
            span_val = max(b, s, g) - min(b, s, g)
            cnt = len(set([b, s, g]))
            pattern = "豹子" if cnt == 1 else ("组三" if cnt == 2 else "组六")
            detail = (
                f"### 福彩3D 第 {issue} 期 官方试机号\n\n"
                f"- **试机号码**：`{sjh}`\n"
                f"- **和值**：{sum_val}（尾：{sum_val % 10}）\n"
                f"- **跨度**：{span_val}\n"
                f"- **形态**：{pattern}\n"
            )
        else:
            detail = f"福彩3D 第 {issue} 期 试机号获取异常或尚未发布。"

        return f"福彩3D试机号：{sjh}", detail

    except Exception as e:
        return "福彩3D试机号抓取失败", f"运行异常：{str(e)}"


def send_wechat(title, content):
    """通过 Server酱 发送微信通知"""
    key = os.environ.get("PUSH_KEY")
    if not key:
        print("未检测到 PUSH_KEY，取消推送")
        return

    push_url = f"https://sctapi.ftqq.com/{key}.send"
    data = urllib.parse.urlencode({"title": title, "desp": content}).encode(
        "utf-8"
    )

    req = urllib.request.Request(push_url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("推送返回结果：", resp.read().decode("utf-8"))


if __name__ == "__main__":
    title, content = fetch_3d_data()
    send_wechat(title, content)
