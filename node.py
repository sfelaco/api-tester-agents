from dotenv import load_dotenv

load_dotenv()

from langchain import hub
from langchain.agents import create_react_agent
from langchain_core.tools import tool
from langchain_openai.chat_models import ChatOpenAI
from state import AgentState
from langchain_experimental.tools import PythonREPLTool
from langchain_core.prompts import HumanMessagePromptTemplate

react_prompt = hub.pull("langchain-ai/react-agent-template")

with open("prompts/code_generator.prompt", "r", encoding="utf8") as file:
    instructions = file.read()
    
instructions = HumanMessagePromptTemplate.from_template_file("prompts/code_generator.prompt", input_variables=[])
prompt = react_prompt.partial(instructions = instructions.prompt.template)

llm = ChatOpenAI(model="gpt-4.1", temperature=0)
tools = [PythonREPLTool()]
react_reasoning_runnable = create_react_agent(llm, tools, prompt)



def run_agent_reasoning_engine(state: AgentState):
    agent_outcome = react_reasoning_runnable.invoke(state)
    return {"agent_outcome": agent_outcome}


# def run_pythonREPLTool(state: AgentState) {
#     PythonREPLTool()invoke(state["agent_outcome"])
# }

def execute_tools(state: AgentState):
    agent_action = state["agent_outcome"]
    
    # Estrai il nome del tool e l'input
    tool_name = agent_action.tool
    tool_input = agent_action.tool_input
    
    # Trova il tool corretto nella lista tools
    selected_tool = None
    for tool in tools:
        if tool.name == tool_name:
            selected_tool = tool
            break
    
    if selected_tool:
        # Esegui il tool selezionato con l'input fornito
        output = selected_tool.invoke(tool_input)
    else:
        output = f"Error: Tool '{tool_name}' not found"
    
    return {"intermediate_steps": [(agent_action, str(output))]}