import json
from datetime import datetime
from agent import graph

def safe_serialize(obj):
    """安全地序列化对象，处理不可JSON序列化的类型"""
    if hasattr(obj, 'content'):  # AIMessage 或其他消息对象
        return {"type": obj.__class__.__name__, "content": str(obj.content)}
    elif hasattr(obj, '__dict__'):  # 其他复杂对象
        return {"type": obj.__class__.__name__, "data": str(obj)}
    elif isinstance(obj, (list, tuple)):
        return [safe_serialize(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: safe_serialize(value) for key, value in obj.items()}
    else:
        return obj

def print_message_content(data, verbose=True):
    """专门用于打印 message content 的函数"""
    if not isinstance(data, dict) or 'messages' not in data:
        print("❌ 数据中没有找到 messages 字段")
        return
    
    messages = data['messages']
    if not messages:
        print("❌ messages 列表为空")
        return
    
    print("\n" + "="*80)
    print("📝 MESSAGE CONTENT:")
    print("="*80)
    
    for i, message in enumerate(messages):
        print(f"\n--- Message {i+1} ---")
        
        # 处理不同类型的消息格式
        if isinstance(message, dict):
            # 字典格式的消息
            msg_type = message.get('type', message.get('role', 'unknown'))
            content = message.get('content', '')
            
            if verbose:
                print(f"类型: {msg_type}")
                print(f"内容长度: {len(str(content))} 字符")
                print("内容:")
            
            print("-" * 40)
            print(content)
            print("-" * 40)
            
        elif hasattr(message, 'content'):
            # 对象格式的消息（如 AIMessage）
            if verbose:
                print(f"类型: {message.__class__.__name__}")
                print(f"内容长度: {len(str(message.content))} 字符")
                print("内容:")
            
            print("-" * 40)
            print(message.content)
            print("-" * 40)
        else:
            print(f"未知消息格式: {type(message)}")
            print(str(message))
    
    print("="*80 + "\n")

def log_step(step_name, data, step_number=None):
    """打印格式化的步骤日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = f"[{timestamp}]"
    if step_number:
        prefix += f" 步骤 {step_number}:"
    
    print(f"\n{'='*60}")
    print(f"{prefix} {step_name}")
    print(f"{'='*60}")
    
    # 如果是 finalize_answer 步骤，专门打印 message content
    if step_name.startswith("✅ finalize_answer") or "finalize" in step_name.lower():
        print_message_content(data, verbose=False)
    
    # 特别关注 sources_gathered 字段
    i = 0
    if isinstance(data, dict) and 'sources_gathered' in data:
        i += 1
        if i > 2:
            return
        print(f"🔍 sources_gathered 调试信息:")
        sources = data['sources_gathered']
        print(f"  - 类型: {type(sources)}")
        print(f"  - 长度: {len(sources) if sources else 0}")
        if sources:
            print(f"  - 内容预览: {sources[:2] if len(sources) > 2 else sources}")
        else:
            print(f"  - 内容: 空列表/None")
        print()
    
    # 如果数据太大，只显示关键信息
    if isinstance(data, dict):
        # 显示状态的关键字段
        key_fields = ['messages', 'query_list', 'search_query', 'web_research_result', 
                     'research_loop_count', 'is_sufficient', 'knowledge_gap', 'follow_up_queries',
                     'sources_gathered']
        filtered_data = {}
        for key in key_fields:
            if key in data:
                value = data[key]
                # 截断过长的内容
                if isinstance(value, str) and len(value) > 200:
                    filtered_data[key] = value[:200] + "..."
                elif isinstance(value, list) and len(value) > 3:
                    # 对于 sources_gathered，显示更多信息用于调试
                    if key == 'sources_gathered':
                        filtered_data[key] = value  # 显示完整信息
                    else:
                        filtered_data[key] = value[:3] + ["..."]
                else:
                    filtered_data[key] = value
        
        if filtered_data:
            try:
                # 尝试安全序列化
                safe_data = safe_serialize(filtered_data)
                # print(json.dumps(safe_data, indent=2, ensure_ascii=False))
            except Exception as e:
                # 如果还是出错，就用简单的字符串表示
                print("数据内容:")
                for key, value in filtered_data.items():
                    print(f"  {key}: {str(value)[:300]}{'...' if len(str(value)) > 300 else ''}")
    
    print(f"{'='*60}\n")

# 初始化参数
initial_state = {
    "messages": [{"role": "user", "content": "分析一下巴菲特最近的持仓变化，整理成优美的网页"}], 
    "max_research_loops": 30, 
    "initial_search_query_count": 30
}

print(f"\n🚀 开始执行智能体流程...")
print(f"初始输入: {initial_state['messages'][0]['content']}")
print(f"最大研究循环次数: {initial_state['max_research_loops']}")
print(f"初始搜索查询数量: {initial_state['initial_search_query_count']}")

step_counter = 0

# 使用 stream 方法来跟踪每个步骤
try:
    for step in graph.stream(initial_state):
        step_counter += 1
        
        # 获取当前步骤的节点名称和数据
        node_name = list(step.keys())[0] if step else "unknown"
        node_data = step.get(node_name, {})
        
        # 根据节点类型显示不同的日志信息
        if node_name == "generate_query":
            log_step("🔍 generate_query", node_data, step_counter)
        elif node_name == "web_research":
            log_step("🌐 web_research", node_data, step_counter)
        elif node_name == "reflection":
            log_step("🤔 reflection", node_data, step_counter)
        elif node_name == "finalize_answer":
            log_step("✅ finalize_answer", node_data, step_counter)
        else:
            log_step(f"📝 执行节点: {node_name}", node_data, step_counter)

    print(f"\n🎉 智能体流程执行完成！总共执行了 {step_counter} 个步骤。")

except Exception as e:
    print(f"\n❌ 执行过程中出现错误: {str(e)}")
    print(f"错误类型: {type(e).__name__}")
    import traceback
    traceback.print_exc()