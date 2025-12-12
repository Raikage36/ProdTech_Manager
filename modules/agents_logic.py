# modules/agents_logic.py
import pandas as pd
from modules.database_manager import insert_many, fetch_all, execute_query

def load_agents_from_excel(filepath):
    """Load agent info from Excel and return as list of tuples."""
    df = pd.read_excel(filepath)
    df = df.fillna("")
    agents = [tuple(row) for row in df.to_numpy()]
    return agents

def save_agents_to_db(agent_list):
    """Bulk insert agents into the database."""
    query = "INSERT INTO agents (name, department, email) VALUES (?, ?, ?)"
    insert_many(query, agent_list)

def get_all_agents():
    """Retrieve all agents from database."""
    return fetch_all("SELECT name, department, email FROM agents")

def update_agent_field(agent_name, field, new_value):
    """Update a single field for an agent."""
    valid_fields = {"name", "department", "email"}
    if field not in valid_fields:
        raise ValueError("Invalid field name")
    query = f"UPDATE agents SET {field} = ? WHERE name = ?"
    execute_query(query, (new_value, agent_name))
