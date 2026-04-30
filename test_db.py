import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect(
            user='postgres.juxvmzccqbroqcoleobp',
            password='DH98ZW0BlCe4zV6C',
            database='postgres',
            host='aws-1-ap-south-1.pooler.supabase.com',
            port=5432,
            ssl='require',
            timeout=10
        )
        print("✓ Connection successful!")
        await conn.close()
    except Exception as e:
        print(f"✗ Connection failed: {type(e).__name__}: {e}")

if __name__ == '__main__':
    asyncio.run(test_connection())
