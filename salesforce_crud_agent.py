"""
Author: Ankit Ghosh
Date: October 2025
"""
import os
import uuid
import asyncio
import gradio as gr
from pprint import pprint
from dotenv import load_dotenv
from langsmith import traceable
from openai import RateLimitError
from langchain_openai import ChatOpenAI
from langchain.globals import set_debug
# from langsmith.wrappers import wrap_openai
from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient

# set_verbose(True)
set_debug(True)
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=1000, api_key=openai_api_key, max_retries=1, stream_usage=True)
# , verbose=True

# google_api_key = os.getenv("GOOGLE_API_KEY")
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",google_api_key=google_api_key, temperature=0, max_tokens=None, max_retries=2,)

async def return_tools():
    
    try:
        client = MultiServerMCPClient(
            {
                "Salesforce": {
                    "transport": "streamable_http",
                    "url": "http://127.0.0.1:7000/mcp",
                }
            }
        )
        # client = MultiServerMCPClient(
        #     {
        #         "Salesforce": {
        #             "transport": "stdio",
        #             "command": "python",
        #             "args": ["aap0_mcp_server.py"],
        #         }
        #     }
        # )
        tools = await client.get_tools()
        return tools
    except Exception as e:
        print(f"Exception in loading tools: {str(e)}")
        return None

tools = asyncio.run(return_tools())
if tools:
    print("#########################\nTools loaded successfully\n#########################")
    pprint(tools)

template = """
System Instruction:
You are a Salesforce Expert Assistant.
Your sole purpose is to answer user queries strictly related to Salesforce topics and data of the salesforce org.
You must not respond to or engage with any questions outside the scope of Salesforce.
You have access to the following tool(s):
{tools}

When handling Salesforce-related queries:
If you are not able to answer the user's question directly, you must use the appropriate tool(s) to retrieve the necessary information from the user's Salesforce org.
Some objects are related to other objects using master-detail or lookup relationship, if you cannot get the user's data by querying one object then use tool(s) to query related objects.

Tool Selection:
Choose the most appropriate tool based on the user's Salesforce-related request and the data needed from their Salesforce org.
Parameter Collection:
Before invoking any tool that requires specific input parameters, explicitly ask the user for all mandatory parameters.
For example, if a tool requires a “location” and a “date”, ask:
“What location and date would you like to use for this request?”
Do not call the tool until all required parameters have been clearly provided by the user.
Properly escape any special characters in user-provided parameters to ensure correct tool invocation.

Salesforce Object & Field API Names:
Retrieve API names for objects and fields from the provided tool(s), don't ask the user for API names.
When constructing Salesforce Object Query Language (SOQL) queries or creating records, always use accurate API names obtained using the given tool(s).
SOQL Query Construction Rules:
Construct SOQL queries automatically based on the user's request.
Always ensure that:
The correct object API names and field API names are used.
The query is syntactically valid and optimized according to Salesforce standards.
Do not display or ask the user to review the SOQL query.
You do not need to ask the user to review or confirm your SOQL query before execution — just construct it yourself using the API names and best practices.
Only ask the user for the field values not the field names.

When creating a record for a Salesforce object:
Ask the user only for the values they want each field to have.
Before proceeding, ensure you have gathered all required fields for that object.

When a user asks for information about a specific Salesforce object, you must:
Identify the primary object mentioned in the user's message (e.g., Account, Opportunity, Case, Product etc.).
Automatically determine related objects that have a lookup or master-detail relationship with the primary object by using Salesforce schema or metadata.
Query related objects as needed to fully answer the user's request — for example, if the user asks for Products, also retrieve related Product feature or product option if they help answer the question.
If the user's intent implies cross-object data (e.g., “show all Contacts for Accounts with closed Opportunities”), dynamically build and execute queries joining or traversing related objects via relationship fields.

Summary of Core Directives:
Only handle Salesforce-related queries.
Use the provided tool(s) responsibly and only after obtaining all required parameters.
Retrieve object and field API names using the tool(s), don't ask the user for API names.
Construct SOQL queries yourself — do not ask for user validation.
When creating records, only request the values for fields, not the field names.
"""

prompt = PromptTemplate.from_template(template)
formatted_prompt = prompt.format(tools=tools)

agent = create_react_agent(llm, tools, prompt=formatted_prompt, checkpointer=InMemorySaver())
#  debug=True,

thread_id = str(uuid.uuid4())

@traceable
async def handle_user_input(message, history):
    if not message.strip():
        raise gr.Error("Your input cannot be empty!")
    try:
        response = await agent.ainvoke(
            {
                "messages": [{"role": "user", "content": message}]
            },
            {
                "configurable": {"thread_id": thread_id}
            }
        )
        # if response["messages"][-3].tool_calls:
        #     print(f"Tool call details: {response["messages"][-3].tool_calls}")
        # if response["messages"][-2].content:
        #     print(f"Tool response: {response1["messages"][-2].content}")
        # print("###################\nFull response start\n###################")
        # pprint(response["messages"])
        # print("#################\nFull response end\n#################")
        return response["messages"][-1].content
        # ["messages"][-1]
    except Exception as rle:
        return f"Exception occurred: {str(rle)}"
        # return f"Rate limit exceeded. Please try again later. {rle}"
    # response.text

initial_history = [
    {"role": "assistant", "content": "Greetings salesforce user.\nI am a salesforce agent of your org.\nYou can ask me any questions related to salesforce topic, as well as about the data in your org."}
]

gr.ChatInterface(
    fn=handle_user_input,
    chatbot=gr.Chatbot(value=initial_history, type="messages"),
    title="Salesforce Agent",
).launch(server_name="127.0.0.1", server_port= 7001)