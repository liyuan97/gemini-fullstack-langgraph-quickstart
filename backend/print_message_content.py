#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 示例数据结构
data = {
    "messages": [
        {
            "type": "AIMessage",
            "content": "# The Feud Between Elon Musk and Donald Trump in June 2025\n\n## Introduction\nIn early June 2025, a public feud erupted between Elon Musk and President Donald Trump, primarily revolving around Musk's criticism of Trump's \"Big Beautiful Act,\" a tax and spending bill. This conflict escalated on social media platforms, particularly X (formerly Twitter), where both figures exchanged insults and accusations. The feud not only highlighted their personal disagreements but also raised concerns about the implications for Tesla and Musk's business interests, including potential impacts on government contracts and stock prices.\n\n## Body\nThe feud began around June 5, 2025, shortly after Musk resigned from his position as head of the Department of Government Efficiency (DOGE). Musk criticized Trump's bill, labeling it a \"disgusting abomination\" and arguing that it would exacerbate the budget deficit and undermine efforts to reduce wasteful spending. In response, Trump expressed disappointment, claiming Musk had initially supported the bill and threatened to cancel government contracts with Musk's companies, including Tesla and SpaceX.\n\nThe exchanges on social media became increasingly heated, with Musk asserting that Trump could not have won the election without his support, while Trump accused Musk of ingratitude. Musk made a controversial claim linking Trump to the Jeffrey Epstein files, which he later deleted, possibly in an attempt to de-escalate the situation. Trump's reaction included dismissing the feud as unimportant and suggesting he might sell a Tesla gifted to him by Musk.\n\nThe fallout from this feud had immediate financial repercussions for Tesla, with the company's stock price dropping significantly amid investor concerns about the potential loss of government contracts and subsidies. Tesla's shares fell by 14% in a single day, wiping out over $150 billion in market value. This decline was compounded by ongoing controversies surrounding Tesla's Autopilot and Full Self-Driving (FSD) systems, which faced scrutiny from regulatory bodies and public skepticism.\n\nDespite the tensions, there were signs of a potential reconciliation as both Musk and Trump expressed a desire to move past the conflict, wishing each other well towards the end of the week. However, the long-term implications of their feud remain uncertain, particularly regarding Tesla's future in the evolving regulatory landscape and its reliance on government support.\n\n## Conclusion\nThe feud between Elon Musk and Donald Trump in June 2025 encapsulated a complex interplay of personal rivalry and significant business implications. As Musk criticized Trump's legislative efforts, the resulting backlash affected Tesla's stock and raised questions about the future of government contracts essential for Musk's ventures. While there were indications of a cooling in tensions, the potential for lasting impacts on Tesla's market position and regulatory environment remains a critical concern for investors and stakeholders alike. The situation underscores the intricate relationship between politics and business in today's landscape, particularly for companies like Tesla that are heavily reliant on government support."
        }
    ],
    "sources_gathered": []
}

def print_message_content_simple():
    """简单打印 content"""
    print("=== 方法1: 简单打印 ===")
    content = data["messages"][0]["content"]
    print(content)
    print()

def print_message_content_formatted():
    """格式化打印 content"""
    print("=== 方法2: 格式化打印 ===")
    content = data["messages"][0]["content"]
    print("Message Content:")
    print("-" * 50)
    print(content)
    print("-" * 50)
    print()

def print_message_content_with_info():
    """带消息信息的打印"""
    print("=== 方法3: 带消息信息打印 ===")
    message = data["messages"][0]
    print(f"Message Type: {message['type']}")
    print(f"Content Length: {len(message['content'])} characters")
    print("\nContent:")
    print("=" * 80)
    print(message["content"])
    print("=" * 80)
    print()

def print_message_content_lines():
    """按行打印 content（便于阅读Markdown格式）"""
    print("=== 方法4: 按行打印（适合Markdown） ===")
    content = data["messages"][0]["content"]
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        print(f"{i:2d}: {line}")
    print()

def print_message_content_truncated(max_length=500):
    """截断打印（用于长文本预览）"""
    print("=== 方法5: 截断打印 ===")
    content = data["messages"][0]["content"]
    if len(content) > max_length:
        truncated = content[:max_length] + "..."
        print(f"Content (first {max_length} characters):")
        print(truncated)
    else:
        print("Content (full):")
        print(content)
    print()

def print_all_messages_content():
    """打印所有消息的 content"""
    print("=== 方法6: 打印所有消息 ===")
    for i, message in enumerate(data["messages"]):
        print(f"Message {i+1} ({message['type']}):")
        print("-" * 40)
        print(message["content"])
        print("-" * 40)
        print()

if __name__ == "__main__":
    print("演示不同的 message content 打印方式:\n")
    
    # 选择你需要的打印方式
    print_message_content_simple()
    print_message_content_formatted()
    print_message_content_with_info()
    print_message_content_lines()
    print_message_content_truncated()
    print_all_messages_content() 