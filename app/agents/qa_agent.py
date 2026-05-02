# app/agents/qa_agent.py (最终修复版)
"""
使用LangGraph构建核心的、自适应的GraphRAG问答代理。
该代理能够分析用户问题，动态选择检索策略（简单或复杂），
并基于从知识图谱中检索到的上下文，合成包含来源引用的答案。
"""
import json
import sys
import traceback
from typing import List, TypedDict, Optional, Union
from pydantic.v1 import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from app.data_access.graph_db import graph_db
from app.providers.llm_provider import turbo_llm, max_llm
from app.services.caching_service import get_cache_service, COLLECTION_NAME
from app.prompts import QUERY_ANALYZER_SYSTEM_PROMPT, SYNTHESIS_SYSTEM_PROMPT


# --- (AgentState, Handler, Router 定义保持不变) ---
class AgentState(TypedDict):
    original_question: str
    route: str
    rewritten_question: Optional[str] = None
    entities: Optional[List[str]] = None
    retrieved_context: Optional[str] = None
    final_answer: Optional[str] = None
    final_sources: Optional[List[dict]] = None
    error_message: Optional[str] = None


class SimpleQuestionHandler(BaseModel):
    """处理简单的、单一主题的问题"""
    rewritten_question: str = Field(description="对原始问题的清晰、独立的改写。")
    entities: List[str] = Field(description="从问题中抽出的核心实体名词列表。")


class ComplexQuestionHandler(BaseModel):
    """处理复杂的、涉及多个主题或需要广泛背景知识的问题"""
    rewritten_question: str = Field(description="对原始问题进行优化和清晰化的改写，使其更适合进行向量检索。")


class ConversationalHandler(BaseModel):
    """处理非知识性的问候、感谢或闲聊"""
    response: str = Field(description="一句礼貌性的、非知识性的回复。",
                          default="您好，我是您的智能学业助手，很乐意回答与计算机知识相关的问题。")


class Router(BaseModel):
    """根据用户问题，选择一个最合适的处理工具。"""
    selected_tool: Union[SimpleQuestionHandler, ComplexQuestionHandler, ConversationalHandler] = Field(...,
                                                                                                       description="为用户问题选择的最合适的处理工具。")



async def query_analysis_node(state: AgentState) -> AgentState:
    print("---AGENT: 正在分析查询...---", file=sys.stderr, flush=True)
    try:
        structured_llm = turbo_llm.with_structured_output(Router)
        prompt = ChatPromptTemplate.from_messages([("system", QUERY_ANALYZER_SYSTEM_PROMPT), ("human", "{question}")])
        chain = prompt | structured_llm
        router_result = await chain.ainvoke({"question": state["original_question"]})
        tool_choice = router_result.selected_tool

        if isinstance(tool_choice, SimpleQuestionHandler):
            print(f"---AGENT: 查询被路由到 'simple' -> entities: {tool_choice.entities}---", file=sys.stderr,
                  flush=True)
            state['route'] = 'simple'
            state['rewritten_question'] = tool_choice.rewritten_question
            state['entities'] = tool_choice.entities
        elif isinstance(tool_choice, ComplexQuestionHandler):
            print(f"---AGENT: 查询被路由到 'complex' -> rewritten: {tool_choice.rewritten_question}---",
                  file=sys.stderr, flush=True)
            state['route'] = 'complex'
            state['rewritten_question'] = tool_choice.rewritten_question
        elif isinstance(tool_choice, ConversationalHandler):
            print("---AGENT: 查询被路由到 'conversational'---", file=sys.stderr, flush=True)
            state['route'] = 'conversational'
            state['final_answer'] = tool_choice.response
            state['final_sources'] = []
        else:
            raise TypeError(f"LLM的Router返回了未知的工具类型: {type(tool_choice)}")
    except Exception as e:
        print(f"---AGENT: 查询分析节点出错: {e}---", file=sys.stderr, flush=True)
        traceback.print_exc()
        state['route'] = 'error'
        state['error_message'] = "抱歉，在理解您的问题时发生了错误。"
    return state


async def simple_retrieval_node(state: AgentState) -> AgentState:
    print("---AGENT: 正在执行简单检索...---", file=sys.stderr, flush=True)
    cache_service = get_cache_service()
    if getattr(cache_service, "client", None) is None:
        state['retrieved_context'] = ""
        return state
    entry_point_ids = []
    entities = state.get('entities', [])
    if not entities:
        state['retrieved_context'] = "抱歉，我没有从您的问题中识别出明确的核心概念以进行检索。"
        return state
    for entity in entities:
        search_results = await cache_service.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=cache_service._get_embedding_model().encode(entity).tolist(),
            limit=1,
            score_threshold=0.70
        )
        if search_results and search_results[0].payload and 'node_id' in search_results[0].payload:
            entry_point_ids.append(search_results[0].payload['node_id'])
    if not entry_point_ids:
        state['retrieved_context'] = "抱歉，在我的知识库中找不到与您问题相关的核心概念。"
    else:
        unique_ids = list(set(entry_point_ids))
        print(f"---AGENT: 发现{len(unique_ids)}个入口点: {unique_ids}---", file=sys.stderr, flush=True)
        context = await graph_db.get_neighborhood(node_ids=unique_ids, hops=1)
        state['retrieved_context'] = context
    return state


async def complex_retrieval_node(state: AgentState) -> AgentState:
    print("---AGENT: 正在执行复杂检索...---", file=sys.stderr, flush=True)
    cache_service = get_cache_service()
    if getattr(cache_service, "client", None) is None:
        state['retrieved_context'] = ""
        return state
    search_results = await cache_service.client.search(
        collection_name=COLLECTION_NAME,
        query_vector=cache_service._get_embedding_model().encode(state['rewritten_question']).tolist(),
        limit=3,
        score_threshold=0.65
    )
    if not search_results:
        state['retrieved_context'] = "抱歉，在我的知识库中找不到与您问题相关的信息。"
        return state
    entry_point_ids = [p.payload['node_id'] for p in search_results if p.payload and 'node_id' in p.payload]
    if not entry_point_ids:
        state['retrieved_context'] = "抱歉，在我的知识库中找不到与您问题相关的有效信息。"
    else:
        unique_ids = list(set(entry_point_ids))
        print(f"---AGENT: 发现{len(unique_ids)}个入口点: {unique_ids}---", file=sys.stderr, flush=True)
        context = await graph_db.get_neighborhood(node_ids=unique_ids, hops=1)
        state['retrieved_context'] = context
    return state


async def conversational_node(state: AgentState) -> AgentState:
    print("---AGENT: 正在处理对话闲聊...---", file=sys.stderr, flush=True)
    state['final_answer'] = "您好，我是您的智能学业助手，很乐意回答与计算机知识相关的问题。"
    state['final_sources'] = []
    return state


async def synthesis_node(state: AgentState) -> AgentState:
    print("---AGENT: 正在合成最终答案...---", file=sys.stderr, flush=True)
    retrieved_context = state.get('retrieved_context', '没有检索到任何上下文信息。')

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", SYNTHESIS_SYSTEM_PROMPT), ("human", "上下文信息:\n```{context}```\n\n原始问题:\n```{question}```")])

    parser = JsonOutputParser()
    chain = prompt_template | max_llm | parser

    try:
        response_data = await chain.ainvoke({"context": retrieved_context, "question": state['original_question']})

        state['final_answer'] = response_data.get('answer', "无法生成格式化的答案。")
        state['final_sources'] = response_data.get('sources', [])
    # vvvvvvvvvvvv 【核心修正：捕获正确的异常类型】 vvvvvvvvvvvv
    except OutputParserException as e:
        # ^^^^^^^^^^^^ 【核心修正结束】 ^^^^^^^^^^^^
        print(f"---AGENT: 答案合成失败，官方解析器也无法处理LLM的输出: {e}---", file=sys.stderr, flush=True)
        raw_output = e.llm_output if hasattr(e, 'llm_output') else str(e)
        state['final_answer'] = raw_output.strip().replace("```json", "").replace("```", "")
        state['final_sources'] = []

    return state


# --- (error_node, route_logic, build_agent_graph, run_agent 保持不变) ---
async def error_node(state: AgentState) -> AgentState:
    print("---AGENT: 进入错误处理流程...---", file=sys.stderr, flush=True)
    state['final_answer'] = state.get('error_message', '处理您的问题时发生了一个未知错误。')
    state['final_sources'] = []
    return state


def route_logic(state: AgentState) -> str:
    route = state.get('route', 'error')
    print(f"---AGENT: 路由决策 -> {route}---", file=sys.stderr, flush=True)
    return route


def build_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("query_analyzer", query_analysis_node)
    workflow.add_node("simple_retriever", simple_retrieval_node)
    workflow.add_node("complex_retriever", complex_retrieval_node)
    workflow.add_node("conversational", conversational_node)
    workflow.add_node("synthesizer", synthesis_node)
    workflow.add_node("error_handler", error_node)

    workflow.set_entry_point("query_analyzer")

    workflow.add_conditional_edges("query_analyzer", route_logic,
                                   {"simple": "simple_retriever", "complex": "complex_retriever",
                                    "conversational": "conversational", "error": "error_handler"})

    workflow.add_edge("simple_retriever", "synthesizer")
    workflow.add_edge("complex_retriever", "synthesizer")
    workflow.add_edge("synthesizer", END)
    workflow.add_edge("conversational", END)
    workflow.add_edge("error_handler", END)
    return workflow.compile()


agent_executor = build_agent_graph()


async def run_agent(question: str) -> dict:
    initial_state = {"original_question": question}
    try:
        print("---AGENT: Starting agent direct invocation...", file=sys.stderr, flush=True)
        final_state = await agent_executor.ainvoke(initial_state, config=RunnableConfig(recursion_limit=5))
        print(f"---AGENT: Invocation ended. Final state captured: {final_state}", file=sys.stderr, flush=True)
        return {"answer": final_state.get('final_answer', "代理执行完毕，但没有最终答案。"),
                "sources": final_state.get('final_sources', [])}
    except Exception as e:
        print(f"---AGENT: 代理执行时发生严重错误: {e}---", file=sys.stderr, flush=True)
        traceback.print_exc()
        return {"answer": "抱歉，我在处理您的问题时遇到了一个严重的内部错误。", "sources": []}
