"""
Author: Ankit Ghosh
Date: October 2025
"""
import os
import sys
from dotenv import load_dotenv
from mcp.server import FastMCP
from langchain_core.tools import tool
from langchain_salesforce import SalesforceTool

load_dotenv()
sd = os.getenv("SALESFORCE_DOMAIN")
sun = os.getenv("SALESFORCE_USERNAME")
spw = os.getenv("SALESFORCE_PASSWORD")
sst = os.getenv("SALESFORCE_SECURITY_TOKEN")

salesforce_tool = SalesforceTool(
    username=sun,
    password=spw,
    security_token=sst,
    domain=sd
)

mcp = FastMCP("Salesforce", host="127.0.0.1", port=7000)

@mcp.tool()
def get_objects_count()-> str:
    """Returns the count of or the number of total objects in the org
    """
    try:
        request = {"operation": "list_objects"}
        result = salesforce_tool.invoke(request)
        objs = [obj['name'] for obj in result if obj['custom'] == True or obj['searchable'] == True]
        return str(len(objs))
    except Exception as e:
        print(str(e))
        return str(e)

@mcp.tool()
def get_objects_list()-> str:
    """Returns the list of total objects in the org as their API names
    """
    try:
        request = {"operation": "list_objects"}
        result = salesforce_tool.invoke(request)
        objs = [obj['name'] for obj in result if obj['custom'] == True or obj['searchable'] == True]
        return str(objs)
    except Exception as e:
        print(str(e))
        return str(e)

@mcp.tool()
def get_standard_objects_count()-> str:
    """Returns the count of or the number of standard objects in the org
    """
    try:
        request = {"operation": "list_objects"}
        result = salesforce_tool.invoke(request)
        objs = [obj['name'] for obj in result if obj['custom'] == True or obj['searchable'] == True]
        std_objs = [obj for obj in objs if not obj.endswith('__c')]
        return str(len(std_objs))
    except Exception as e:
        print(str(e))
        return str(e)

@mcp.tool()
def get_standard_objects_list()-> str:
    """Returns the complete list of standard objects in the org
    """
    try:
        request = {"operation": "list_objects"}
        result = salesforce_tool.invoke(request)
        objs = [obj['name'] for obj in result if obj['custom'] == True or obj['searchable'] == True]
        std_objs = [obj for obj in objs if not obj.endswith('__c')]
        return str(std_objs)
    except Exception as e:
        print(str(e))
        return str(e)

@mcp.tool()
def get_fields_of_object(object: str) -> str:
    """Returns the list of fields(API names) of the object passed as an input.
    Requires: 'object'.
    The object's API name is given by the AI assistant using other tools before calling this tool.
    """
    try:
        request = {"operation": "describe", "object_name": object}
        result = salesforce_tool.invoke(request)
        list = result['fields']
        # [res['name'] for res in result['fields'] if res['custom'] == True or res['updateable'] == True]
        return str(list)
    except Exception as e:
        print("###########################\nException on getting fields\n###########################\n"+str(e))
        return str(e)

@mcp.tool()
def get_records_count(object: str) -> str:
    """Returns the count of all the records of the object passed as an input.
    Requires: 'object'.
    The object's API name is given by the AI assistant using other tools before calling this tool.
    """
    try:
        request = {"operation": "query", "query": f"SELECT COUNT() FROM {object}"}
        result = salesforce_tool.invoke(request)
        return str(result['totalSize'])
    except Exception as e:
        print("############################\nException on getting records\n############################\n"+str(e))
        return str(e)

@mcp.tool()
def execute_soql_query(soql_query: str) -> str:
    """Executes the SOQL query passed as an input and returns the result.
    Requires: 'soql_query'.
    The SOQL query is given by the AI assistant before calling this tool.
    """
    try:
        request = {"operation": "query", "query": soql_query}
        result = salesforce_tool.invoke(request)
        return str(result)
    except Exception as e:
        print("#################\nException on SOQL\n#################\n"+str(e))
        return str(e)

@mcp.tool()
def create_record_of_object(object: str, fields: dict) -> str:
    """Creates a record of the object passed as an input with the fields and their values passed as a dictionary.
    Requires: 'object', 'fields'.
    The API names of the object and the fields is given by the AI assistant before calling this tool. 
    The user only provides the values for fields not the field names before calling this tool.
    """
    try:
        request = {"operation": "create", "object_name": object,"record_data":fields}
        result = salesforce_tool.invoke(request)
        return str(result)
    except Exception as e:
        print("###################\nException on create\n###################\n"+str(e))
        return str(e)

@mcp.tool()
def update_record_of_object(object: str, record_id: str, fields: dict) -> str:
    """Updates a record of the object passed as an input with the fields and their values passed as a dictionary.
    Requires: 'object', 'record_id', 'fields'.
    The API names of the object and the fields and the record_id is given by the AI assistant before calling this tool. 
    The user only provides the values for fields not the field names before calling this tool.
    """
    try:
        request = {"operation": "update", "object_name": object,"record_id":record_id,"record_data":fields}
        result = salesforce_tool.invoke(request)
        return str(result)
    except Exception as e:
        print("###################\nException on update\n###################\n"+str(e))
        return str(e)

@mcp.tool()
def delete_record_of_object(object: str, record_id: str) -> str:
    """Deletes a record of the object passed as an input.
    Requires: 'object', 'record_id'.
    The API name of the object and the record_id is given by the AI assistant before calling this tool. 
    """
    try:
        request = {"operation": "delete", "object_name": object,"record_id":record_id}
        result = salesforce_tool.invoke(request)
        return str(result)
    except Exception as e:
        print("###################\nException on delete\n###################\n"+str(e))
        return str(e)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
    # streamable-http