
from langchain_core.agents import AgentFinish
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv
from state import AgentState
from node import run_agent_reasoning_engine, run_pythonREPLTool
from node import execute_tools
from langchain_community.document_loaders import TextLoader
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

from consts import CLIENT_EXECUTOR_TOOL, REACT_AGENT, EXECUTOR


load_dotenv()

max_iterations = 4

def should_continue(state: AgentState) -> str:
    iteration = state.get("iteration", 0)
    if isinstance(state["agent_outcome"], AgentFinish) or iteration >= max_iterations:
        return END
    else:
        state["number_iterations"] = iteration + 1
        return CLIENT_EXECUTOR_TOOL

def start_agentic_flow(file_path: str):
    flow = StateGraph(AgentState)
    flow.set_entry_point(REACT_AGENT)
    flow.add_node(REACT_AGENT, run_agent_reasoning_engine)
    flow.add_node(CLIENT_EXECUTOR_TOOL, execute_tools)
    flow.add_node(EXECUTOR, run_pythonREPLTool)

    
    flow.add_conditional_edges(
        REACT_AGENT,
        should_continue,
    )
    flow.add_edge(CLIENT_EXECUTOR_TOOL, EXECUTOR)
    flow.add_edge(EXECUTOR,REACT_AGENT)
    

    app = flow.compile()
    #app.get_graph().draw_mermaid_png(output_file_path="graph.png")

    loader = TextLoader(file_path= file_path, encoding="utf8")
    documents = loader.load()
    file_text = documents[0].page_content
    
    input = HumanMessage(content=f"""Voglio creare ed eseguire un applicazione di test di queste API: {file_path}, 
                         se ci sono errori correggili rigenerando il codice e rieseguelo. Se l'applicazione deve ritornare
                         il mumero di record salvati nel DB, se il dato non è presente rigenera il codice e riesegui""")
    
    res = app.invoke({"input": input,
                      "file_text": file_text})    
    print(res["agent_outcome"])    

if __name__ == "__main__":
    start_agentic_flow("openapi/example.yaml")