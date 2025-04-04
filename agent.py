import os
from typing import Dict, Any, List, Optional

from langchain_ollama import OllamaLLM
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.chains.conversation.memory import ConversationBufferMemory

# Define database path consistently
DB_FILE = "employee_database.db"
DB_URI = f"sqlite:///{DB_FILE}"

# Check if database exists after initialization
if not os.path.exists(DB_FILE):
    raise FileNotFoundError(f"Database file {DB_FILE} not found. Please ensure the database is created.")

# Initialize the Ollama LLM
llm = OllamaLLM(model="gemma3:12b", temperature=0.5)

# Connect to the SQLite database with debug info
try:
    db = SQLDatabase.from_uri(
        DB_URI,
        sample_rows_in_table_info=2  # Include sample rows to help the agent understand data structure
    )
    # Verify database connection by checking tables
    tables = db.get_usable_table_names()
    if not tables:
        print(f"WARNING: No tables found in database {DB_URI}")
    else:
        print(f"Successfully connected to database. Found tables: {tables}")
except Exception as e:
    print(f"Error connecting to database: {e}")
    raise

# Create the SQLDatabaseToolkit with explicit db and llm
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Explicitly get tools from the toolkit
tools = toolkit.get_tools()

# Memory storage for conversations by conversation_id
conversation_memories = {}

# Define a better prompt template that includes more context about the database and conversation history
prompt = PromptTemplate.from_template(
    """You are an AI assistant that helps retrieve and provide information about employees from a SQL database.

You have access to the following tools: {tools}

Previous conversation history:
{chat_history}

IMPORTANT GUIDELINES:
1. First, check what tables are available using the list_tables tool
2. Get the schema for relevant tables using the get_schema tool
3. Formulate a SQL query to answer the question
4. Execute the query and interpret the results
5. If you encounter errors, check the schema again and fix your query
6. If you are unable to get the proper information or think the information is wrong, say so
7. Reference any information from previous parts of our conversation when relevant
8. When referring to people, use their full names on first mention, then you can use first names
9. Be friendly and conversational in your responses, not overly technical
10. Format any numerical values appropriately (currency with $ sign, percentages, etc.)

This database contains information about employees including their:
- name
- department
- position
- salary
- years of service

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
Thought: {agent_scratchpad}"""
)

# Create the ReAct agent with the improved prompt
agent = create_react_agent(llm, tools, prompt)


def get_conversation_memory(conversation_id: str) -> ConversationBufferMemory:
    """
    Get or create conversation memory for a specific conversation ID.

    Args:
        conversation_id: Unique identifier for the conversation.

    Returns:
        A ConversationBufferMemory instance for the conversation.
    """
    if conversation_id not in conversation_memories:
        conversation_memories[conversation_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )

    return conversation_memories[conversation_id]


def process_agent_query(query: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a query using the LangChain agent with conversation memory.

    Args:
        query: The query string from the user.
        conversation_id: Optional unique identifier for the conversation.

    Returns:
        A dictionary containing the agent's response and any retrieved information.
    """
    try:
        # If no conversation ID is provided, generate a random one
        if not conversation_id:
            import uuid
            conversation_id = str(uuid.uuid4())

        # Get or create memory for this conversation
        memory = get_conversation_memory(conversation_id)

        # Create a new agent executor with the memory
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=8,
            memory=memory,
            return_intermediate_steps=True
        )

        # Execute the query
        result = agent_executor.invoke({
            "input": query,
        })

        # Include full details in the response
        response = {
            "conversation_id": conversation_id,
            "query": query,
            "response": result["output"],
            "steps": [
                {
                    "tool": step[0].tool,
                    "input": step[0].tool_input,
                    "output": step[1]
                } for step in result.get("intermediate_steps", [])
            ],
            "success": True
        }

        # For debugging purposes, print chat history length
        chat_history = memory.chat_memory.messages
        print(f"Conversation {conversation_id} has {len(chat_history)} messages")

    except Exception as e:
        response = {
            "conversation_id": conversation_id,
            "query": query,
            "response": f"Error processing your query: {str(e)}",
            "steps": [],
            "success": False
        }

    return response