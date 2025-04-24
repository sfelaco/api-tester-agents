from dotenv import load_dotenv

load_dotenv()

from langchain import hub
from langchain.agents import create_react_agent
from langchain_core.tools import tool
from langchain_openai.chat_models import ChatOpenAI
from state import AgentState
from langchain_experimental.tools import PythonREPLTool
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_core.output_parsers import StrOutputParser

react_prompt = hub.pull("langchain-ai/react-agent-template")

#react_prompt = hub.pull("hwchase17/react")


instructions_template = HumanMessagePromptTemplate.from_template_file("prompts/code_generator.prompt", input_variables=[""])    

prompt = react_prompt.partial(instructions = instructions_template.format().content)
llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0)


 
generation_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template_file("prompts/system_message.prompt", input_variables=[""]),
        HumanMessagePromptTemplate(prompt = prompt)
     ]
)   

tools = [ PythonREPLTool()]
react_reasoning_runnable = create_react_agent(llm, tools, generation_prompt)


def run_agent_reasoning_engine(state: AgentState):
    agent_outcome = react_reasoning_runnable.invoke(state)
    return {"agent_outcome": agent_outcome}


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
        if selected_tool.name == "generate_python_code":
            output = selected_tool.invoke(state['file_text'])
        else:
             output = selected_tool.invoke(tool_input)
    else:
        output = f"Error: Tool '{tool_name}' not found"
    
    iteration = state.get("number_iterations", 0)
    
    return {"intermediate_steps": [(agent_action, str(output))],
            "number_iterations": iteration+1}


if __name__ == "__main__":
     ("openapi/example.yaml")