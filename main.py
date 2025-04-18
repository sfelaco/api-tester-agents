
from langchain_core.agents import AgentFinish
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv
from state import AgentState
from node import run_agent_reasoning_engine
from node import execute_tools
from langchain_community.document_loaders import TextLoader


from consts import CLIENT_EXECUTOR_TOOL, CLIENT_GENERATOR_AGENT


load_dotenv()


def should_continue(state: AgentState) -> str:
    if isinstance(state["agent_outcome"], AgentFinish):
        return END
    else:
        return CLIENT_EXECUTOR_TOOL

if __name__ == "__main__":
    flow = StateGraph(AgentState)
    flow.add_node(CLIENT_GENERATOR_AGENT, run_agent_reasoning_engine)
    flow.add_node(CLIENT_EXECUTOR_TOOL, execute_tools)

    flow.set_entry_point(CLIENT_GENERATOR_AGENT)
    flow.add_conditional_edges(
        CLIENT_GENERATOR_AGENT,
        should_continue,
    )
    flow.add_edge(CLIENT_EXECUTOR_TOOL,CLIENT_GENERATOR_AGENT)

    app = flow.compile()
    app.get_graph().draw_mermaid_png(output_file_path="graph.png")

    loader = TextLoader(file_path= "openapi/example.yaml", encoding="utf8")
    documents = loader.load()
    file_text = documents[0].page_content

    res = app.invoke({"input": f" ```{file_text}```"})
    print(res["agent_outcome"])
    