# import traceback
import psycopg2
from psycopg2 import pool, extras
from psycopg2 import sql
# from contextlib import contextmanager
# from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple
# from langchain_core.runnables import RunnableConfig
# from typing import Any, Dict, Optional, Iterator, AsyncIterator
# from datetime import datetime, timezone
# # Configure logging
from loguru import logger
import os
db_username = os.getenv('DB_USERNAME')
db_host = os.getenv('DB_HOST')
db = os.getenv('DB_NAME')
db_password = os.getenv('DB_PASSWORD')
db_port = os.getenv('DB_PORT')
db_drivername = os.getenv('DB_DRIVERNAME')
db_port = int(db_port)

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
from psycopg_pool import ConnectionPool
# Connection configuration
connection_kwargs =  {
    "autocommit": True,
    "prepare_threshold": 0,
    "keepalives": 1,  # Enable keepalives
    "keepalives_idle": 30,  # Send keepalive after 30 seconds of inactivity
    "keepalives_interval": 10,  # Retransmit keepalive after 10 seconds
    "keepalives_count": 5,  # Close connection after 5 failed keepalives
}
# Connection string
conninfo = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db}"

# Create a global connection pool
pool = ConnectionPool(
    conninfo=conninfo,
    max_size=20,
    kwargs=connection_kwargs,
)


checkpointer = PostgresSaver(pool)


checkpointer.setup()





# pool = ConnectionPool(
#     # Example configuration
#     conninfo = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db}",
#     max_size=20,
# )

# Uses the pickle module for serialization
# Make sure that you're only de-serializing trusted data
# (e.g., payloads that you have serialized yourself).
# Or implement a custom serializer.
# memory= PostgresCheckpoint(
#     serializer=PickleCheckpointSerializer(),
#     sync_connection=pool,
# )
# # import threading
# # class PostgresSaver(BaseCheckpointSaver):
# #     def __init__(self, connection):
# #         super().__init__()
# #         self.connection = connection
# #         logger.info("PostgresSaver initialized")

# #     @classmethod
# #     def from_conn_string(cls, conn_string):
# #         logger.info("Creating PostgresSaver from connection string")
# #         try:
# #             connection = psycopg2.connect(conn_string)
# #             logger.info("Database connection established successfully")
# #             return cls(connection)
# #         except Exception as e:
# #             logger.error(f"Failed to create database connection: {str(e)}")
# #             logger.error(traceback.format_exc())
# #             raise

# #     @contextmanager
# #     def cursor(self):
# #         logger.debug("Getting database cursor")
# #         cursor = self.connection.cursor()
# #         try:
# #             yield cursor
# #             self.connection.commit()
# #             logger.debug("Transaction committed successfully")
# #         except Exception as e:
# #             self.connection.rollback()
# #             logger.error(f"Database transaction failed: {str(e)}")
# #             logger.error(traceback.format_exc())
# #             raise
# #         finally:
# #             cursor.close()
# #             logger.debug("Cursor closed")
            
# #     def get_latest_timestamp(self, thread_id: str) -> str:
# #         with self.cursor() as cursor:
# #             select_query = sql.SQL(
# #                 "SELECT thread_ts FROM checkpoints WHERE thread_id = %s ORDER BY thread_ts DESC LIMIT 1"
# #             )
# #             cursor.execute(select_query, (thread_id,))
# #             result = cursor.fetchone()
# #             return result[0] if result else None
        

# #     def setup(self) -> None:
# #         logger.info("Setting up checkpoints table")
# #         try:
# #             with self.cursor() as cursor:
# #                 create_table_query = """
# #                 CREATE TABLE IF NOT EXISTS checkpoints (
# #                     thread_id TEXT NOT NULL,
# #                     thread_ts TEXT NOT NULL,
# #                     parent_ts TEXT,
# #                     checkpoint BYTEA,
# #                     metadata BYTEA,
# #                     PRIMARY KEY (thread_id, thread_ts)
# #                 );
# #                 """
# #                 cursor.execute(create_table_query)
# #                 logger.info("Checkpoints table created/verified successfully")
# #         except Exception as e:
# #             logger.error(f"Failed to setup checkpoints table: {str(e)}")
# #             logger.error(traceback.format_exc())
# #             raise
# class PostgresSaver(BaseCheckpointSaver):
#     def __init__(self, connection_pool):
#         super().__init__()
#         self._pool = connection_pool
#         self._local = threading.local()
#         logger.info("PostgresSaver initialized with connection pool")

#     @classmethod
#     def from_conn_string(cls, conn_string, min_conn=1, max_conn=10):
#         """Create a new instance with a connection pool"""
#         try:
#             connection_pool = psycopg2.pool.ThreadedConnectionPool(
#                 minconn=min_conn,
#                 maxconn=max_conn,
#                 dsn=conn_string
#             )
#             logger.info(f"Created connection pool (min={min_conn}, max={max_conn})")
#             return cls(connection_pool)
#         except Exception as e:
#             logger.error(f"Failed to create connection pool: {str(e)}")
#             logger.error(traceback.format_exc())
#             raise

#     @contextmanager
#     def get_connection(self):
#         """Get a connection from the pool with automatic reconnection"""
#         conn = None
#         try:
#             conn = self._pool.getconn()
#             # Test if connection is alive
#             conn.cursor().execute('SELECT 1')
#             yield conn
#         except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
#             logger.warning(f"Connection error, attempting to reconnect: {str(e)}")
#             if conn:
#                 self._pool.putconn(conn, close=True)
#             # Try to get a new connection
#             conn = self._pool.getconn()
#             yield conn
#         except Exception as e:
#             logger.error(f"Database error: {str(e)}")
#             logger.error(traceback.format_exc())
#             raise
#         finally:
#             if conn:
#                 self._pool.putconn(conn)

#     @contextmanager
#     def cursor(self):
#         """Get a cursor with automatic connection management"""
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
#             try:
#                 yield cursor
#                 conn.commit()
#                 # logger.debug("Transaction committed successfully")
#             except Exception as e:
#                 conn.rollback()
#                 logger.error(f"Database transaction failed: {str(e)}")
#                 logger.error(traceback.format_exc())
#                 raise
#             finally:
#                 cursor.close()

#     def setup(self) -> None:
#         """Setup the database table with retry logic"""
#         max_retries = 3
#         for attempt in range(max_retries):
#             try:
#                 with self.cursor() as cursor:
#                     create_table_query = """
#                     CREATE TABLE IF NOT EXISTS checkpoints (
#                         thread_id TEXT NOT NULL,
#                         thread_ts TEXT NOT NULL,
#                         parent_ts TEXT,
#                         checkpoint BYTEA,
#                         metadata BYTEA,
#                         PRIMARY KEY (thread_id, thread_ts)
#                     );
#                     """
#                     cursor.execute(create_table_query)
#                     logger.info("Checkpoints table created/verified successfully")
#                     break
#             except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
#                 if attempt == max_retries - 1:
#                     raise
#                 logger.warning(f"Setup attempt {attempt + 1} failed, retrying: {str(e)}")

#     def get_latest_timestamp(self, thread_id: str) -> Optional[str]:
#         """Get the latest timestamp with retry logic"""
#         max_retries = 3
#         for attempt in range(max_retries):
#             try:
#                 with self.cursor() as cursor:
#                     select_query = sql.SQL(
#                         "SELECT thread_ts FROM checkpoints WHERE thread_id = %s ORDER BY thread_ts DESC LIMIT 1"
#                     )
#                     cursor.execute(select_query, (thread_id,))
#                     result = cursor.fetchone()
#                     return result[0] if result else None
#             except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
#                 if attempt == max_retries - 1:
#                     raise
#                 logger.warning(f"Get timestamp attempt {attempt + 1} failed, retrying: {str(e)}")

#     # def put(self, config: RunnableConfig, checkpoint: dict, metadata: dict, *args, **kwargs) -> RunnableConfig:
#     #     logger.info(f"Putting checkpoint for config: {config}")
#     #     # logger.debug(f"Checkpoint data: {checkpoint}")
#     #     # logger.debug(f"Metadata: {metadata}")
#     #     # logger.debug(f"Additional args: {args}")
#     #     # logger.debug(f"Additional kwargs: {kwargs}")
        
#     #     try:
            
#     #         thread_id = config["configurable"]["thread_id"]
#     #         thread_ts = datetime.now(timezone.utc).isoformat()
#     #         parent_ts = config["configurable"].get("thread_ts")
            
#     #         # logger.debug(f"Thread ID: {thread_id}")
#     #         # logger.debug(f"Thread TS: {thread_ts}")
#     #         # logger.debug(f"Parent TS: {parent_ts}")

#     #         with self.cursor() as cursor:
#     #             insert_query = sql.SQL(
#     #                 """
#     #                 INSERT INTO checkpoints (thread_id, thread_ts, parent_ts, checkpoint, metadata)
#     #                 VALUES (%s, %s, %s, %s, %s)
#     #                 ON CONFLICT (thread_id, thread_ts) DO UPDATE
#     #                 SET parent_ts = EXCLUDED.parent_ts, 
#     #                     checkpoint = EXCLUDED.checkpoint, 
#     #                     metadata = EXCLUDED.metadata
#     #                 """
#     #             )
                
#     #             serialized_checkpoint = self.serde.dumps(checkpoint)
#     #             serialized_metadata = self.serde.dumps(metadata)
                
#     #             logger.debug("Executing insert query")
#     #             cursor.execute(
#     #                 insert_query,
#     #                 (
#     #                     thread_id,
#     #                     thread_ts,
#     #                     parent_ts,
#     #                     serialized_checkpoint,
#     #                     serialized_metadata,
#     #                 ),
#     #             )
#     #             logger.info("Checkpoint stored successfully")

#     #         return {
#     #             "configurable": {
#     #                 "thread_id": thread_id,
#     #                 "thread_ts": thread_ts,
#     #             }
#     #         }
#     #     except Exception as e:
#     #         logger.error(f"Failed to store checkpoint: {str(e)}")
#     #         logger.error(traceback.format_exc())
#     #         raise

#     def put(self, config: RunnableConfig, checkpoint: dict, metadata: dict, *args, **kwargs) -> RunnableConfig:
#         logger.info(f"Putting checkpoint for config: {config}")
        
#         try:
#             thread_id = config["configurable"]["thread_id"]
#             thread_ts = datetime.now(timezone.utc).isoformat()
#             parent_ts = config["configurable"].get("thread_ts")
            
#             # Ensure checkpoint has proper structure
#             if not isinstance(checkpoint, dict):
#                 checkpoint = {"channel_values": checkpoint}

#             with self.cursor() as cursor:
#                 insert_query = sql.SQL(
#                     """
#                     INSERT INTO checkpoints (thread_id, thread_ts, parent_ts, checkpoint, metadata)
#                     VALUES (%s, %s, %s, %s, %s)
#                     ON CONFLICT (thread_id, thread_ts) DO UPDATE
#                     SET parent_ts = EXCLUDED.parent_ts, 
#                         checkpoint = EXCLUDED.checkpoint, 
#                         metadata = EXCLUDED.metadata
#                     """
#                 )
                
#                 serialized_checkpoint = self.serde.dumps(checkpoint)
#                 serialized_metadata = self.serde.dumps(metadata)
                
#                 cursor.execute(
#                     insert_query,
#                     (
#                         thread_id,
#                         thread_ts,
#                         parent_ts,
#                         serialized_checkpoint,
#                         serialized_metadata,
#                     ),
#                 )
#                 logger.info("Checkpoint stored successfully")

#             return {
#                 "configurable": {
#                     "thread_id": thread_id,
#                     "thread_ts": thread_ts,
#                 }
#             }
#         except Exception as e:
#             logger.error(f"Failed to store checkpoint: {str(e)}")
#             logger.error(traceback.format_exc())
#             raise

        
#     def put_writes(self, config: RunnableConfig, writes: Dict[str, Any], *args, **kwargs) -> RunnableConfig:
#         """Store writes in the checkpoint system."""
#         logger.info(f"Putting writes for config: {config}")
#         logger.debug(f"Writes data: {writes}")
        
#         try:
#             thread_id = config["configurable"]["thread_id"]
#             thread_ts = datetime.now(timezone.utc).isoformat()
#             parent_ts = config["configurable"].get("thread_ts")
            
#             with self.cursor() as cursor:
#                 insert_query = sql.SQL(
#                     """
#                     INSERT INTO checkpoints (thread_id, thread_ts, parent_ts, checkpoint, metadata)
#                     VALUES (%s, %s, %s, %s, %s)
#                     ON CONFLICT (thread_id, thread_ts) DO UPDATE
#                     SET parent_ts = EXCLUDED.parent_ts, 
#                         checkpoint = EXCLUDED.checkpoint, 
#                         metadata = EXCLUDED.metadata
#                     """
#                 )
                
#                 # Store writes as checkpoint data
#                 serialized_checkpoint = self.serde.dumps(writes)
#                 metadata = {"type": "writes"}
#                 serialized_metadata = self.serde.dumps(metadata)
                
#                 cursor.execute(
#                     insert_query,
#                     (
#                         thread_id,
#                         thread_ts,
#                         parent_ts,
#                         serialized_checkpoint,
#                         serialized_metadata,
#                     ),
#                 )
#                 logger.info("Writes stored successfully")

#             return {
#                 "configurable": {
#                     "thread_id": thread_id,
#                     "thread_ts": thread_ts,
#                 }
#             }
#         except Exception as e:
#             logger.error(f"Failed to store writes: {str(e)}")
#             logger.error(traceback.format_exc())
#             raise

#     async def aput_writes(self, config: RunnableConfig, writes: Dict[str, Any],  *args, **kwargs) -> RunnableConfig:
#         """Async version of put_writes."""
#         return self.put_writes(config, writes)
    

#     # def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
#     #     logger.info(f"Getting tuple for config: {config}")
#     #     try:
#     #         thread_id = config["configurable"]["thread_id"]
#     #         thread_ts = config["configurable"].get(
#     #             "thread_ts", self.get_latest_timestamp(thread_id)
#     #         )

#     #         with self.cursor() as cursor:
#     #             select_query = sql.SQL(
#     #                 "SELECT checkpoint, metadata, parent_ts FROM checkpoints WHERE thread_id = %s AND thread_ts = %s"
#     #             )
#     #             cursor.execute(select_query, (thread_id, thread_ts))
#     #             result = cursor.fetchone()
                
#     #             if result:
#     #                 checkpoint, metadata, parent_ts = result
#     #                 logger.info("Checkpoint tuple found")
#     #                 return CheckpointTuple(
#     #                     config,
#     #                     self.serde.loads(bytes(checkpoint)),
#     #                     self.serde.loads(bytes(metadata)),
#     #                     (
#     #                         {
#     #                             "configurable": {
#     #                                 "thread_id": thread_id,
#     #                                 "thread_ts": parent_ts,
#     #                             }
#     #                         }
#     #                         if parent_ts
#     #                         else None
#     #                     ),
#     #                 )
#     #             logger.info("No checkpoint tuple found")
#     #             return None
#     #     except Exception as e:
#     #         logger.error(f"Failed to get tuple: {str(e)}")
#     #         logger.error(traceback.format_exc())
#         #         raise
#     def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
#         logger.info(f"Getting tuple for config: {config}")
#         try:
#             thread_id = config["configurable"]["thread_id"]
#             thread_ts = config["configurable"].get(
#                 "thread_ts", self.get_latest_timestamp(thread_id)
#             )

#             if not thread_ts:
#                 logger.info("No checkpoint found")
#                 return None

#             with self.cursor() as cursor:
#                 select_query = sql.SQL(
#                     "SELECT checkpoint, metadata, parent_ts FROM checkpoints WHERE thread_id = %s AND thread_ts = %s"
#                 )
#                 cursor.execute(select_query, (thread_id, thread_ts))
#                 result = cursor.fetchone()
                
#                 if result:
#                     checkpoint_bytes, metadata_bytes, parent_ts = result
                    
#                     # Properly deserialize the checkpoint and metadata
#                     try:
#                         checkpoint = self.serde.loads(bytes(checkpoint_bytes))
#                         metadata = self.serde.loads(bytes(metadata_bytes))
                        
#                         # Ensure checkpoint is a dictionary with required structure
#                         if not isinstance(checkpoint, dict):
#                             checkpoint = {"channel_values": checkpoint}
                        
#                         logger.info("Checkpoint tuple found and deserialized")
#                         return CheckpointTuple(
#                             config,
#                             checkpoint,
#                             metadata,
#                             {
#                                 "configurable": {
#                                     "thread_id": thread_id,
#                                     "thread_ts": parent_ts,
#                                 }
#                             } if parent_ts else None,
#                         )
#                     except Exception as e:
#                         logger.error(f"Deserialization error: {str(e)}")
#                         return None
                        
#                 logger.info("No checkpoint tuple found")
#                 return None
                
#         except Exception as e:
#             logger.error(f"Failed to get tuple: {str(e)}")
#             logger.error(traceback.format_exc())
#             raise
        
#     async def aput(self, config: RunnableConfig, checkpoint: dict, metadata: dict, *args, **kwargs) -> RunnableConfig:
#         logger.info("Executing async put")
#         return self.put(config, checkpoint, metadata, *args, **kwargs)
    

#     def close(self):
#         """Close the connection pool"""
#         logger.info("Closing connection pool")
#         try:
#             self._pool.closeall()
#             logger.info("Connection pool closed successfully")
#         except Exception as e:
#             logger.error(f"Error closing connection pool: {str(e)}")
#             logger.error(traceback.format_exc())
#             raise
#     # def close(self):
#     #     logger.info("Closing database connection")
#     #     try:
#     #         self.connection.close()
#     #         logger.info("Database connection closed successfully")
#     #     except Exception as e:
#     #         logger.error(f"Error closing database connection: {str(e)}")
#     #         logger.error(traceback.format_exc())
#     #         raise

# conn_string = (
#     f"dbname={db} user={db_username} password={db_password} "
#     f"host={db_host} port={db_port}"
# )
# memory = PostgresSaver.from_conn_string(conn_string,min_conn=1,
#     max_conn=10)
# # memory.setup()
# # Test connection function with logging
# def test_db_connection(conn_string):
#     logger.info("Testing database connection")
#     try:
#         conn = psycopg2.connect(conn_string)
#         cur = conn.cursor()
#         cur.execute('SELECT version();')
#         version = cur.fetchone()
#         logger.info("Successfully connected to the database!")
#         logger.info(f"PostgreSQL version: {version[0]}")
#         cur.close()
#         conn.close()
#         return True
#     except Exception as e:
#         logger.error(f"Database connection test failed: {str(e)}")
#         logger.error(traceback.format_exc())
#         return False


# Uses the pickle module for serialization
# Make sure that you're only de-serializing trusted data
# (e.g., payloads that you have serialized yourself).
# Or implement a custom serializer.
