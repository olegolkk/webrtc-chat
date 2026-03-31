#!/usr/bin/env python
"""
Скрипт для инициализации базы данных.
Создает все таблицы, определенные в моделях SQLAlchemy.
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PATH для импорта модулей
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.db.base import Base
from app.core.config import settings
from app.models import User, Room, Message  # Импортируем модели для регистрации


async def init_database():
    """Создание всех таблиц в базе данных"""
    print("=" * 50)
    print("Initializing database...")
    print(f"Database URL: {settings.DATABASE_URL}")
    print("=" * 50)

    # Создаем движок
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,  # Показываем SQL запросы
        future=True
    )

    try:
        # Создаем все таблицы
        async with engine.begin() as conn:
            print("\nCreating tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("✓ Tables created successfully!")

        print("\n" + "=" * 50)
        print("Database initialization completed!")
        print("=" * 50)

        # Выводим список созданных таблиц
        print("\nCreated tables:")
        for table in Base.metadata.tables.keys():
            print(f"  - {table}")

    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        raise
    finally:
        await engine.dispose()


async def drop_database():
    """Удаление всех таблиц (осторожно!)"""
    confirm = input("\n⚠️  This will DELETE all data! Are you sure? (yes/no): ")
    if confirm.lower() != "yes":
        print("Operation cancelled.")
        return

    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    try:
        async with engine.begin() as conn:
            print("\nDropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)
            print("✓ All tables dropped successfully!")
    except Exception as e:
        print(f"\n❌ Error dropping database: {e}")
        raise
    finally:
        await engine.dispose()


async def recreate_database():
    """Пересоздание базы данных (удалить и создать заново)"""
    await drop_database()
    await init_database()


async def check_database():
    """Проверка подключения к базе данных"""
    print("Checking database connection...")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    try:
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            print("✓ Database connection successful!")

            # Проверяем существующие таблицы
            result = await conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            tables = result.fetchall()

            if tables:
                print("\nExisting tables:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\nNo tables found. Run 'python init_db.py init' to create them.")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database management for WebRTC Chat")
    parser.add_argument(
        "command",
        nargs="?",
        default="init",
        choices=["init", "drop", "recreate", "check"],
        help="Command to execute"
    )

    args = parser.parse_args()

    if args.command == "init":
        asyncio.run(init_database())
    elif args.command == "drop":
        asyncio.run(drop_database())
    elif args.command == "recreate":
        asyncio.run(recreate_database())
    elif args.command == "check":
        asyncio.run(check_database())