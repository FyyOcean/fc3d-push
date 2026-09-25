import os
import re
import urllib.parse
import urllib.request


def fetch_3d_data():
    """精确抓取彩之家最新试机号（兼容单球拆分排版与机球信息）"""
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

        # 1. 精确定位主区域的期号（如：福彩3d第2026257期）
        issue_match = re.search(r"第(202\d{4})期(?:3d)?试机号", html)
        issue = (
            issue_match.group(1)
            if issue_match
            else re.search(r"202\d{4}", html).group(0)
        )

        # 2. 定位机球信息（如：1机1球 / 2机1球）
        jq_match = re.search(r"([12]机[1234]球)", html)
        jq_info = jq_match.group(1) if jq_match else "暂无"

        # 3. 精确定位三个开奖球（彩之家将三个球拆开放在 <li> 或 <span> 中）
        # 截取从“3d试机号”到“机球”之间的核心 HTML 片段
        snippet_match = re.search(
            r"3d试机号[：:\s]*([\s\S]{1,300}?)本期机球", html
        )
        sjh = ""
        if snippet_match:
            digits = re.findall(r">(\d)<", snippet_match.group(1))
            if len(digits) >= 3:
                sjh = f"{digits[0]}{digits[1]}{digits[2]}"

        # 若拆分未截取到，使用备选连续数字匹配
        if not sjh:
            alt_match = re.search(
                r'class="[^"]*sjh[^"]*"[^>]*>(\d{3})<', html
            )
            if alt_match:
                sjh = alt_match.group(1)

        # 4. 计算走势特征并拼接推送卡片
        if len(sjh) == 3 and sjh.isdigit():
            b, s, g = int(sjh[0]), int(sjh[1]), int(sjh[2])
            sum_val = b + s + g
            span_val = max(b, s, g) - min(b, s, g)
            cnt = len(set([b, s, g]))
            pattern = "豹子" if cnt == 1 else ("组三" if cnt == 2 else "组六")

            detail = (
                f"### 福彩3D 第 {issue} 期 官方试机号\n\n"
                f"- **试机号码**：`{sjh}`\n"
                f"- **机球配置**：{jq_info}\n"
                f"- **和值**：{sum_val}（尾：{sum_val % 10}）\n"
                f"- **跨度**：{span_val}\n"
                f"- **形态**：{pattern}\n"
            )
        else:
            detail = f"福彩3D 第 {issue} 期 试机号尚未摇出（通常 18:25~18:30 更新）。"

        return f"福彩3D试机号：{sjh}", detail

    except Exception as e:
        return "福彩3D试机号抓取失败", f"运行异常：{str(e)}"


def send_wechat(title, content):
    """通过 Server酱 发送微信通知"""
    key = os.environ.get("PUSH_KEY")
    if not key:
        print("未检测到 PUSH_KEY")
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
