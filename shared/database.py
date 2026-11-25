

import asyncpg

from pgvector.asyncpg import register_vector

from shared.config import settings

pool : asyncpg.Pool | None = None

async def init_connection(connection:asyncpg.connection):
        
        """
    Register pgvector types for every connection
    created by the connection pool.
    """
        await register_vector(connection)


async def connect_to_database():

        global pool

        pool = await asyncpg.create_pool(
              dsn=settings.database_url,
              min_size=2,
              max_size=2,
              init=init_connection
        )

        print("Database connection pool created")

async def close_database_connection():

        global pool

        if pool is not None:
                await pool.close()

                pool = None

        print("Database connection pool closed")   


async def get_pool() -> asyncpg.Pool:

        if pool is None:

                raise RuntimeError(
                        "Database connection pool is not initialized"
                )

        return pool



