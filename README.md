# Chat with Structured & Unstructured Data 

A lightweight demo combining **Semantic Kernel**, **LangChain SQL tools**, and **Azure AI Search** to power a routed chatbot:
- Interprets natural language into SQL queries and executes them against an Azure SQL `Trades` table.
- Answers concept-driven queries using Azure AI Search.
- Routes user questions between tools using a semantic router.

---

### Application Architecture 
<img width="6825" height="1944" alt="MultiAgent Strucutred   Unstructured Data (SQL + AAIS) - Langchain (1)" src="https://github.com/user-attachments/assets/959df070-884d-40d5-8cde-55b28aeaa3ec" />


### SQL Connection (Semantic Kernel Plugin with Langchain Tool) 
To connect to SQL Database, the LangChain SQLAlchemy tool is wrapped as a Semantic Kernel plugin function. This exposes the SQL execution capability as a skill that the agent can invoke. The tool handles query execution against the connected Azure SQL Database, while Semantic Kernel provides the orchestration layer to call it when a user query requires structured data retrieval.

The exposed function ```sql_retriever``` validates and executes read-only T-SQL ```SELECT``` statements against the ```TransactionTrades``` table in Azure SQL Database.
- Tool: LangChain SQLDatabase (SQLAlchemy engine)
- Function: ```run_sql_query```
- Purpose: Executes validated queries and returns results as JSON objects ```([{"col": value, ...}, ...])```
- Constraints: Only ```SELECT``` queries are allowed, and execution is restricted to the ```TransactionTrades``` table.
  
### How it works 
- Users ask questions in natural language.
- The Router Agent examines the query:
  - Sends data-related queries to ```RunSQLLangchain``` plugin (after SQL generation and validation).
  - Sends AI-concept queries to Azure AI Search plugin.
- The SQL plugin applies safety checks (SELECT only, single table, no DML), executes against the ```Trades``` table, and returns JSON results.
- Responses are formatted cleanly, e.g., as tables via markdown.

##  Features

- **NL → SQL**: Uses a `ChatCompletionAgent` to translate user queries into valid T-SQL SELECT statements and executes them via a secure LangChain plugin (`RunSQLLangchain`).
- **AI Search Integration**: Retrieves and summarizes AI-related content via Azure Cognitive Search when SQL data isn’t relevant.
- **Tool Routing**: Smart router agent picks the right tool based on query content.
- **Frontend**: Chat UI powered by **Chainlit** for interactive experimentation.

---

##  Project Structure
├── app.py                     # Main Chat bot entry point

├── requirements.txt           # Required dependencies

├── sample_env.txt             # Example .env configuration

├── sql_connection/            # SQL connection and validation module

│   └── sqlalchemy_authentication.py

├── sk_plugins/                # Semantic Kernel plugins

│   ├── langchain_sql_db.py    # SQL plugin (RunSQLLangchain)

│   └── ai_search.py           # AI Search plugin

├── tests/                     # Optional: test scripts for connection, sql plugin, etc.

└── data/                      # Example csv data to upload to sql database 

---

##  Setup Instructions

1. **Clone the repository**  
   ```bash
   git clone https://github.com/lana-noor/sk-langchain-sql-aisearch.git
   cd sk-langchain-sql-aisearch
   ```
2. Install dependencies
  ```bash
   pip install -r requirements.txt
   ```
3. Create ```.env``` file from ```sample_env.txt``` and fill in your credentials.
   - You need to have the following services: Azure OpenAI, Azure AI Search index and SQL Database. 
4.  Provide your NL→SQL prompt
   - Customize and save the detailed prompt into ```sql_connection/sql_prompt.txt```.
5. Test SQL Connection and Plugin
   - DB connection tests (SELECT 1, SELECT TOP 1 * FROM Trades)
  ```bash
    python tests/test_sql_connection.py
  ```
   - Plugin behavior tests (valid/invalid SQL scenarios)
  ```bash
    python tests/test_sql_plugin.py
  ```
6. Run the application
```bash
python app.py
chainlit run app.py
```
