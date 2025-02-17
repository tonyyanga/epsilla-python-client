#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Try this simple example
# 1. docker run --pull=always -d -p 8888:8888 epsilla/vectordb
# 2. pip3 install --upgrade pyepsilla
# 3. python3 simple_example.py
#

from pyepsilla import vectordb

# Connect to Epsilla VectorDB
client = vectordb.Client(protocol='http',  host='127.0.0.1',        port='8888')

# You can also use Epsilla Cloud
# client = vectordb.Client(protocol='https', host='demo.epsilla.com', port='443')

# Load DB with path
## pay attention to change db_path to persistent volume for production environment
status_code, response = client.load_db(db_name="MyDB", db_path="/data/epsilla_demo")
print(response)

# Set DB to current DB
client.use_db(db_name="MyDB")

# Create a table with schema in current DB
status_code, response = client.create_table(
  table_name="MyTable",
  table_fields=[
    {"name": "ID", "dataType": "INT", "primaryKey": True},
    {"name": "Doc", "dataType": "STRING"},
    {"name": "Embedding", "dataType": "VECTOR_FLOAT", "dimensions": 4}
  ]
)
print(response)

# Get a list of table names in current DB
status_code, response = client.list_tables()
print(response)

# Insert new vector records into table
status_code, response = client.insert(
  table_name="MyTable",
  records=[
    {"ID": 1, "Doc": "Berlin", "Embedding": [0.05, 0.61, 0.76, 0.74]},
    {"ID": 2, "Doc": "London", "Embedding": [0.19, 0.81, 0.75, 0.11]},
    {"ID": 3, "Doc": "Moscow", "Embedding": [0.36, 0.55, 0.47, 0.94]},
    {"ID": 4, "Doc": "San Francisco", "Embedding": [0.18, 0.01, 0.85, 0.80]},
    {"ID": 5, "Doc": "Shanghai", "Embedding": [0.24, 0.18, 0.22, 0.44]}
  ]
)
print(response)

# Query Vectors with specific response field
status_code, response = client.query(
  table_name="MyTable",
  query_field="Embedding",
  query_vector=[0.35, 0.55, 0.47, 0.94],
  response_fields = ["Doc"],
  limit=2
)

# Query Vectors without specific response field, then it will return all fields
status_code, response = client.query(
  table_name="MyTable",
  query_field="Embedding",
  query_vector=[0.35, 0.55, 0.47, 0.94],
  limit=2
)
print(response)


# status_code, response =  client.delete(table_name="MyTable", ids=[3])
status_code, response =  client.delete(table_name="MyTable", primary_keys=[3, 4])
# status_code, response =  client.delete(table_name="MyTable", filter="Doc <> 'San Francisco'")
print(response)



# Drop table
# status_code, response = client.drop_table("MyTable")
# print(response)

# Unload db
# status_code, response = client.unload_db("MyDB")
# print(response)
