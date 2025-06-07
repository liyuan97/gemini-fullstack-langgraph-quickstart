import os
import time
from typing import Optional

from dotenv import load_dotenv
from google.genai import Client
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from langgraph.types import Send

from agent.configuration import Configuration
from agent.prompts import (
    answer_instructions,
    get_current_date,
    query_writer_instructions,
    reflection_instructions,
    web_searcher_instructions,
    html_prompt,
)
from agent.state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
)
from agent.tools_and_schemas import Reflection, SearchQueryList
from agent.utils import (
    get_citations,
    get_research_topic,
    insert_citation_markers,
    resolve_urls,
)

load_dotenv()

if os.getenv("GEMINI_API_KEY") is None:
    raise ValueError("GEMINI_API_KEY is not set")

# Used for Google Search API
genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))
global_llm  = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0.3,
            max_tokens=64000,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

# Nodes
def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """LangGraph node that generates a search queries based on the User's question.

    Uses Gemini 2.0 Flash to create an optimized search query for web research based on
    the User's question.

    Args:
        state: Current graph state containing the User's question
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated query
    """
    configurable = Configuration.from_runnable_config(config)

    # check for custom initial search query count
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = configurable.number_of_initial_queries

    structured_llm = global_llm.with_structured_output(SearchQueryList)

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        number_queries=state["initial_search_query_count"],
    )
    # Generate the search queries
    result = structured_llm.invoke(formatted_prompt)
    return {"query_list": result.query}


def continue_to_web_research(state: QueryGenerationState):
    """LangGraph node that sends the search queries to the web research node.

    This is used to spawn n number of web research nodes, one for each search query.
    """
    return [
        Send("web_research", {"search_query": search_query, "id": int(idx)})
        for idx, search_query in enumerate(state["query_list"])
    ]


def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """LangGraph node that performs web research using the native Google Search API tool.

    Executes a web search using the native Google Search API tool in combination with Gemini 2.0 Flash.
    Includes retry mechanism for handling network connection issues.

    Args:
        state: Current graph state containing the search query and research loop count
        config: Configuration for the runnable, including search API settings

    Returns:
        Dictionary with state update, including sources_gathered, research_loop_count, and web_research_results
    """
    # Configure
    configurable = Configuration.from_runnable_config(config)
    formatted_prompt = web_searcher_instructions.format(
        current_date=get_current_date(),
        research_topic=state["search_query"],
    )

    # 重试机制参数
    max_retries = 3
    base_delay = 2  # 基础延迟秒数
    
    for attempt in range(max_retries):
        try:
            # Uses the google genai client as the langchain client doesn't return grounding metadata
            response = genai_client.models.generate_content(
                model=configurable.query_generator_model,
                contents=formatted_prompt,
                config={
                    "tools": [{"google_search": {}}],
                    "temperature": 0,
                },
            )
            
            # 如果成功，处理响应并返回结果
            # resolve the urls to short urls for saving tokens and time
            resolved_urls = resolve_urls(
                response.candidates[0].grounding_metadata.grounding_chunks, state["id"]
            )
            # Gets the citations and adds them to the generated text
            citations = get_citations(response, resolved_urls)
            modified_text = insert_citation_markers(response.text, citations)
            sources_gathered = [item for citation in citations for item in citation["segments"]]

            return {
                "sources_gathered": sources_gathered,
                "search_query": [state["search_query"]],
                "web_research_result": [modified_text],
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"🔄 Web research attempt {attempt + 1}/{max_retries} failed: {error_msg}")
            
            # 如果是最后一次尝试，使用备用方案
            if attempt == max_retries - 1:
                print("❌ All attempts failed, using fallback response")
                # 使用 OpenAI 作为备用方案进行简单的文本生成
                try:
                    fallback_llm = ChatOpenAI(
                        model="gpt-4o-mini",
                        temperature=0.1,
                        max_tokens=1000
                    )
                    
                    fallback_prompt = f"""
                    Research the following topic and provide a comprehensive summary:
                    Topic: {state["search_query"]}
                    
                    Please provide:
                    1. Key information about the topic
                    2. Important facts and details
                    3. Current developments or status
                    
                    Note: This is a fallback response due to search API connectivity issues.
                    """
                    
                    fallback_result = fallback_llm.invoke(fallback_prompt)
                    
                    return {
                        "sources_gathered": [{
                            "value": "Fallback response due to API connectivity issues",
                            "short_url": "#fallback",
                            "title": "Fallback Research"
                        }],
                        "search_query": [state["search_query"]],
                        "web_research_result": [f"[备用回复] {fallback_result.content}"],
                    }
                    
                except Exception as fallback_error:
                    print(f"❌ Fallback also failed: {fallback_error}")
                    # 最终备用方案：返回基本信息
                    return {
                        "sources_gathered": [],
                        "search_query": [state["search_query"]],
                        "web_research_result": [f"抱歉，由于网络连接问题，无法完成对 '{state['search_query']}' 的研究。请检查网络连接或稍后重试。"],
                    }
            else:
                # 指数退避延迟
                delay = base_delay * (2 ** attempt)
                print(f"⏳ Waiting {delay} seconds before retry...")
                time.sleep(delay)


def reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """LangGraph node that identifies knowledge gaps and generates potential follow-up queries.

    Analyzes the current summary to identify areas for further research and generates
    potential follow-up queries. Uses structured output to extract
    the follow-up query in JSON format.

    Args:
        state: Current graph state containing the running summary and research topic
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated follow-up query
    """
    configurable = Configuration.from_runnable_config(config)
    # Increment the research loop count and get the reasoning model
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    reasoning_model = state.get("reasoning_model") or configurable.reasoning_model

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )
    result = global_llm.with_structured_output(Reflection).invoke(formatted_prompt)

    return {
        "is_sufficient": result.is_sufficient,
        "knowledge_gap": result.knowledge_gap,
        "follow_up_queries": result.follow_up_queries,
        "research_loop_count": state["research_loop_count"],
        "number_of_ran_queries": len(state["search_query"]),
    }


def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> OverallState:
    """LangGraph routing function that determines the next step in the research flow.

    Controls the research loop by deciding whether to continue gathering information
    or to finalize the summary based on the configured maximum number of research loops.

    Args:
        state: Current graph state containing the research loop count
        config: Configuration for the runnable, including max_research_loops setting

    Returns:
        String literal indicating the next node to visit ("web_research" or "finalize_summary")
    """
    configurable = Configuration.from_runnable_config(config)
    max_research_loops = (
        state.get("max_research_loops")
        if state.get("max_research_loops") is not None
        else configurable.max_research_loops
    )
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        return "web_build"
    else:
        return [
            Send(
                "web_research",
                {
                    "search_query": follow_up_query,
                    "id": state["number_of_ran_queries"] + int(idx),
                },
            )
            for idx, follow_up_query in enumerate(state["follow_up_queries"])
        ]


# def finalize_answer(state: OverallState, config: RunnableConfig):
#     """LangGraph node that finalizes the research summary.

#     Prepares the final output by deduplicating and formatting sources, then
#     combining them with the running summary to create a well-structured
#     research report with proper citations.

#     Args:
#         state: Current graph state containing the running summary and sources gathered

#     Returns:
#         Dictionary with state update, including running_summary key containing the formatted final summary with sources
#     """
#     configurable = Configuration.from_runnable_config(config)
#     reasoning_model = state.get("reflection_model") or configurable.reflection_model

#     # Format the prompt
#     current_date = get_current_date()
#     formatted_prompt = answer_instructions.format(
#         current_date=current_date,
#         research_topic=get_research_topic(state["messages"]),
#         summaries="\n---\n\n".join(state["web_research_result"]),
#     )

#     # init Reasoning Model, default to Gemini 2.5 Flash
#     # llm = ChatGoogleGenerativeAI(
#     #     model=reasoning_model,
#     #     temperature=0,
#     #     max_retries=2,
#     #     api_key=os.getenv("GEMINI_API_KEY"),
#     # )
#     llm = ChatOpenAI(
#             model="gpt-4o-mini",
#             temperature=0.1,
#             max_tokens=2000
#         )
#     llm = ChatAnthropic(
#             model="claude-sonnet-4-20250514",
#             temperature=0.1,
#             max_tokens=2000,
#             api_key=os.getenv("ANTHROPIC_API_KEY"),
#         )
#     result = llm.invoke(formatted_prompt)

#     # Replace the short urls with the original urls and add all used urls to the sources_gathered
#     unique_sources = []
#     for source in state["sources_gathered"]:
#         if source["short_url"] in result.content:
#             result.content = result.content.replace(
#                 source["short_url"], source["value"]
#             )
#             unique_sources.append(source)

#     return {
#         "messages": [AIMessage(content=result.content)],
#         "sources_gathered": unique_sources,
#     }


def web_build(state: OverallState, config: RunnableConfig):
    """LangGraph node that generates an HTML file based on the research results.

    Takes the finalized research content and creates a beautiful HTML page
    with proper styling and structure.

    Args:
        state: Current graph state containing the finalized research content and sources
        config: Configuration for the runnable

    Returns:
        Dictionary with state update, including html_content key containing the generated HTML
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Get the research content from the last message
    research_content = state["messages"][-1].content if state["messages"] else ""
    research_topic = get_research_topic(state["messages"])
    
    # Create the HTML generation prompt
    formatted_html_prompt = html_prompt.format(
        research_topic=research_topic,
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )
    

    # Generate HTML content
    html_result = global_llm.invoke(formatted_html_prompt)
    
    # Save HTML to file
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create filename based on research topic
    safe_filename = "".join(c for c in research_topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_filename = safe_filename.replace(' ', '_')[:50]  # Limit filename length
    html_filename = f"{output_dir}/{safe_filename}_research.html"
    
    # Write HTML content to file
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_result.content)
    
    return {
        "html_content": html_result.content,
        "html_filename": html_filename,
        "messages": state["messages"] + [AIMessage(content=f"HTML报告已生成并保存为: {html_filename}")]
    }


# Create our Agent Graph
builder = StateGraph(OverallState, config_schema=Configuration)

# Define the nodes we will cycle between
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
# builder.add_node("finalize_answer", finalize_answer)
builder.add_node("web_build", web_build)

# Set the entrypoint as `generate_query`
# This means that this node is the first one called
builder.add_edge(START, "generate_query")
# Add conditional edge to continue with search queries in a parallel branch
builder.add_conditional_edges(
    "generate_query", continue_to_web_research, ["web_research"]
)
# Reflect on the web research
builder.add_edge("web_research", "reflection")
# Evaluate the research
builder.add_conditional_edges(
    "reflection", evaluate_research, ["web_research", "web_build"]
)
# Generate HTML report after finalizing answer
# builder.add_edge("finalize_answer", "web_build")
# End after building HTML
builder.add_edge("web_build", END)

graph = builder.compile(name="pro-search-agent")
