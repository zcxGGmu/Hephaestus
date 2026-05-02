#!/usr/bin/env python3
"""
Database setup script
Help quickly configure PostgreSQL database connection and table structure
"""

import asyncio
import os
import sys
from pathlib import Path

async def create_database_if_not_exists(host, port, username, password, database):
    """Create database if it does not exist"""
    try:
        import asyncpg # type: ignore
        
        # Connect to postgres default database
        postgres_url = f"postgresql://{username}:{password}@{host}:{port}/postgres"
        conn = await asyncpg.connect(postgres_url)
        
        # Check if target database exists
        result = await conn.fetchrow(
            "SELECT 1 FROM pg_database WHERE datname = $1", database
        )
        
        if result:
            print(f"Database '{database}' already exists")
        else:
            print(f"Database '{database}' does not exist, creating...")
            # Create database
            await conn.execute(f'CREATE DATABASE "{database}"')
            print(f"Database '{database}' created successfully")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Database creation failed: {e}")
        return False

async def test_database_connection():
    """娴嬭瘯鏁版嵁搴撹繛鎺?""
    print("Test database connection...")
    
    try:
        import asyncpg # type: ignore
        print("asyncpg is installed")
    except ImportError:
        print("asyncpg is not installed, please run: pip install asyncpg")
        return False
    
    # 鑾峰彇鏁版嵁搴撹繛鎺ヤ俊鎭?
    print("\nPlease enter database connection information:")
    host = input("Host address (default: localhost): ").strip() or "localhost"
    port = input("Port (default: 5432): ").strip() or "5432"
    database = input("Database name (default: hephaestus): ").strip() or "hephaestus"
    username = input("Username (default: postgres): ").strip() or "postgres"
    password = input("Password: ").strip()
    
    if not password:
        print("Password cannot be empty")
        return False
    
    # 鏋勫缓杩炴帴瀛楃涓?
    database_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    print(f"\nConnection string: postgresql://{username}:***@{host}:{port}/{database}")
    
    try:
        # 娴嬭瘯杩炴帴
        conn = await asyncpg.connect(database_url)
        print("Database connection successful")
        
        # 娴嬭瘯鏌ヨ
        result = await conn.fetchval("SELECT version()")
        print(f"PostgreSQL version: {result.split(',')[0]}")
        
        await conn.close()
        
        # 淇濆瓨閰嶇疆鍒?env鏂囦欢
        # JWT:锛圝SON Web Token锛夋槸涓€绉嶅紑鏀炬爣鍑嗭紙RFC 7519锛夛紝鐢ㄤ簬鍦ㄤ笉鍚岀郴缁熶箣闂村畨鍏ㄥ湴浼犻€掍俊鎭?
        # 璁╂湇鍔″櫒鍜屽鎴风涔嬮棿瀹夊叏鍦颁紶閫掕韩浠介獙璇佸拰鎺堟潈淇℃伅锛屽父鐢ㄤ簬鐧诲綍鎬佺鐞嗐€丄PI 鎺堟潈銆佸垎甯冨紡绯荤粺鍗曠偣鐧诲綍绛夊満鏅?
        env_content = f"""# Database configuration
DATABASE_URL={database_url}

# JWT configuration
JWT_SECRET_KEY=your-secret-key-change-in-production-{os.urandom(16).hex()}  
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("Configuration saved to .env file")
        return True
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        
        # Try to create database if it doesn't exist
        if "does not exist" in str(e):
            print("Attempting to create database...")
            if await create_database_if_not_exists(host, port, username, password, database):
                print("Retrying connection...")
                try:
                    # Retry connection after creating database
                    conn = await asyncpg.connect(database_url)
                    print("Database connection successful")
                    
                    # Test query
                    result = await conn.fetchval("SELECT version()")
                    print(f"PostgreSQL version: {result.split(',')[0]}")
                    
                    await conn.close()
                    
                    # Save configuration to .env file
                    env_content = f"""# Database configuration
DATABASE_URL={database_url}

# JWT configuration
JWT_SECRET_KEY=your-secret-key-change-in-production-{os.urandom(16).hex()}  
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30
"""
                    
                    with open('.env', 'w', encoding='utf-8') as f:
                        f.write(env_content)
                    
                    print("Configuration saved to .env file")
                    return True
                    
                except Exception as retry_e:
                    print(f"Connection still failed after database creation: {retry_e}")
        
        print("\nCommon solutions:")
        print("1. Check if PostgreSQL service is running")
        print("2. Check if username and password are correct")
        print("3. Check if user has permission to create databases")
        print("4. Check firewall settings")
        return False

async def main():
    """Main function"""
    print("Database setup guide")
    print("=" * 50)
    
    # 姝ラ1: 娴嬭瘯鏁版嵁搴撹繛鎺?
    if not await test_database_connection():
        print("\nDatabase connection failed, please check the configuration and try again")
        return
    
    print("\nDatabase setup completed!")
    print("\nNext you can:")
    print("1. Start FastAPI server: python -m uvicorn api:app --reload")
    print("2. Test API endpoints: POST /api/auth/register")
    print("3. Check the configuration in the .env file")

if __name__ == "__main__":
    asyncio.run(main()) 
