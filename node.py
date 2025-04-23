from dotenv import load_dotenv

load_dotenv()

from langchain import hub
from langchain.agents import create_react_agent
from langchain_core.tools import tool
from langchain_openai.chat_models import ChatOpenAI
from state import AgentState
from langchain_experimental.tools import PythonREPLTool
from langchain_core.prompts import HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.output_parsers import StrOutputParser

react_prompt = hub.pull("langchain-ai/react-agent-template")

#react_prompt = hub.pull("hwchase17/react")

with open("prompts/code_generator.prompt", "r", encoding="utf-8") as file:
    instructions = file.read()
    
instructions_template = HumanMessagePromptTemplate.from_template_file("prompts/code_generator.prompt", input_variables=['file_text'])


prompt = react_prompt.partial(instructions = 
             """Sei un agent che è genera codice Python per eseguire un client OpenAPI, partendo da una specifica alla quale i tool possono accedere.
                Dopo aver generato il codice eseguilo e ritorna l'output dell'applicazione, se ci sono errori correggili e riesegui. """)
#prompt = react_prompt
llm = ChatOpenAI(model="gpt-4.1", temperature=0)
"""Tool for running python code in a REPL."""
    
@tool 
def generate_python_code(yaml_file: str) -> str:
    """Tool for generating python code."""
    prompt = ChatPromptTemplate.from_template(template = instructions_template.prompt.template)
    chain = prompt | llm  | StrOutputParser()
    result = chain.invoke(input = {"file_text": yaml_file})
    return PythonREPLTool().invoke(result)
     


tools = [ generate_python_code]
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
        if selected_tool.name == "generate_python_code":
            output = selected_tool.invoke(state['file_text'])
        else:
             output = selected_tool.invoke(tool_input)
    else:
        output = f"Error: Tool '{tool_name}' not found"
    
    return {"intermediate_steps": [(agent_action, str(output))]}


if __name__ == "__main__":
    generate_python_code("openapi/example.yaml")