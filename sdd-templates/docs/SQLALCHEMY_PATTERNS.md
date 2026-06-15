# SQLAlchemy Async パターン

## 1. 基本セットアップ

### 1.1 Database クラス

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """ORM基底クラス"""
    pass


class Database:
    """データベース接続管理クラス"""

    def __init__(self, url: str):
        self.engine: AsyncEngine = create_async_engine(
            url,
            echo=False,  # 本番では False
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,  # 接続ヘルスチェック
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """セッションのコンテキストマネージャ"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def create_tables(self) -> None:
        """テーブル作成"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """テーブル削除（テスト用）"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def dispose(self) -> None:
        """エンジン終了"""
        await self.engine.dispose()


# シングルトンインスタンス
_db: Database | None = None

def init_db(url: str = "sqlite+aiosqlite:///./data/app.db") -> Database:
    """データベース初期化"""
    global _db
    if _db is None:
        _db = Database(url)
    return _db

def get_db() -> Database:
    """データベースインスタンス取得"""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db
```

### 1.2 FastAPI 依存性注入

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依存性: セッション取得"""
    db = get_db()
    async with db.session() as session:
        yield session

# 使用例
@router.get("/orders")
async def list_orders(
    session: AsyncSession = Depends(get_session)
):
    repo = OrderRepository(session)
    return await repo.list_all()
```

---

## 2. モデル定義パターン

### 2.1 基本モデル（タイムスタンプ付き）

```python
from datetime import UTC, datetime
from uuid import uuid4
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

def utc_now() -> datetime:
    return datetime.now(UTC)

def generate_uuid() -> str:
    return str(uuid4())

class TimestampMixin:
    """タイムスタンプMixin"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        index=True,
    )
```

### 2.2 リレーションシップ

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    buyer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id"),
        index=True,
    )

    # リレーションシップ
    buyer: Mapped["Company"] = relationship(
        back_populates="orders",
        lazy="selectin",  # N+1防止
    )
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
    )

    order: Mapped["Order"] = relationship(back_populates="items")
```

### 2.3 Enum の使用

```python
from enum import Enum
from sqlalchemy import Enum as SQLEnum

class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SHIPPED = "shipped"
    COMPLETED = "completed"

class Order(Base):
    __tablename__ = "orders"

    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, native_enum=False),  # 文字列として保存
        default=OrderStatus.PENDING,
    )
```

---

## 3. リポジトリパターン

### 3.1 基本リポジトリ

```python
from typing import Generic, TypeVar, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    """基本リポジトリ"""

    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: str) -> Optional[T]:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        await self.session.delete(entity)
        await self.session.flush()
```

### 3.2 特化リポジトリ

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

class OrderRepository(BaseRepository[Order]):
    """注文リポジトリ"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    async def get_with_items(self, order_id: str) -> Optional[Order]:
        """注文と明細を一括取得（N+1防止）"""
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_buyer(
        self,
        buyer_id: str,
        status: Optional[OrderStatus] = None,
    ) -> list[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.buyer_id == buyer_id)
        )
        if status:
            stmt = stmt.where(Order.status == status)
        stmt = stmt.order_by(Order.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

---

## 4. N+1 問題の防止

### 4.1 問題のあるコード

```python
# ❌ N+1問題が発生
async def get_orders_bad(session: AsyncSession) -> list[dict]:
    result = await session.execute(select(Order))
    orders = result.scalars().all()

    output = []
    for order in orders:
        # 各orderごとにクエリが発行される
        items = order.items  # lazy load発生
        output.append({"order": order, "items": items})

    return output
```

### 4.2 解決方法

```python
# ✅ selectinload で一括取得
async def get_orders_good(session: AsyncSession) -> list[dict]:
    stmt = select(Order).options(selectinload(Order.items))
    result = await session.execute(stmt)
    orders = result.scalars().all()

    return [{"order": o, "items": o.items} for o in orders]
```

### 4.3 ローディング戦略

| 戦略 | 用途 | SQL |
|------|------|-----|
| `lazy="select"` | デフォルト、必要時に取得 | 個別SELECT |
| `lazy="selectin"` | 関連を一括取得 | SELECT ... WHERE id IN (...) |
| `lazy="joined"` | JOINで取得 | SELECT ... JOIN ... |
| `lazy="subquery"` | サブクエリで取得 | SELECT ... WHERE id IN (SELECT ...) |

```python
# モデル定義でデフォルト設定
items: Mapped[list["OrderItem"]] = relationship(
    lazy="selectin",  # 常にselectinloadを使用
)

# クエリ時にオーバーライド
from sqlalchemy.orm import joinedload

stmt = select(Order).options(joinedload(Order.buyer))
```

---

## 5. トランザクション管理

### 5.1 自動コミット（推奨）

```python
async with db.session() as session:
    repo = OrderRepository(session)
    order = await repo.create(Order(...))
    # コンテキスト終了時に自動コミット
# ここでコミット完了
```

### 5.2 明示的トランザクション

```python
async with db.session() as session:
    async with session.begin():
        # この中で例外が発生するとロールバック
        await session.execute(...)
        await session.execute(...)
    # begin()終了時にコミット
```

### 5.3 ネストトランザクション（Savepoint）

```python
async with db.session() as session:
    order = Order(...)
    session.add(order)

    try:
        async with session.begin_nested():
            # Savepoint開始
            risky_operation()
            # 例外が発生してもここだけロールバック
    except Exception:
        pass  # 親トランザクションは継続

    await session.commit()  # orderはコミットされる
```

---

## 6. テストパターン

### 6.1 pytest フィクスチャ

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def db():
    """テスト用データベース"""
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_tables()
    yield database
    await database.drop_tables()
    await database.dispose()

@pytest.fixture
async def session(db) -> AsyncGenerator[AsyncSession, None]:
    """テスト用セッション（ロールバック付き）"""
    async with db.session() as session:
        yield session
        # テスト後に自動ロールバック
```

### 6.2 テスト例

```python
@pytest.mark.asyncio
async def test_create_order(session: AsyncSession):
    repo = OrderRepository(session)

    order = Order(
        order_number="ORD-001",
        buyer_id="buyer-123",
        status=OrderStatus.PENDING,
    )
    created = await repo.create(order)

    assert created.id is not None
    assert created.order_number == "ORD-001"

    # 取得確認
    found = await repo.get_by_id(created.id)
    assert found is not None
    assert found.order_number == "ORD-001"
```

---

## 7. マイグレーション (Alembic)

### 7.1 セットアップ

```bash
pip install alembic
alembic init migrations
```

### 7.2 alembic.ini 設定

```ini
[alembic]
script_location = migrations
sqlalchemy.url = driver://user:pass@localhost/dbname

# 非同期対応
# sqlalchemy.url を env.py で動的設定
```

### 7.3 env.py (Async対応)

```python
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from src.models import Base

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online():
    import asyncio
    asyncio.run(run_async_migrations())
```

### 7.4 マイグレーション作成

```bash
# 自動生成
alembic revision --autogenerate -m "Add orders table"

# 手動作成
alembic revision -m "Add index on orders.status"
```

### 7.5 マイグレーション実行

```bash
# 最新まで適用
alembic upgrade head

# 1つ戻す
alembic downgrade -1

# 特定リビジョンへ
alembic upgrade abc123
```

---

## 8. 接続プール設定

| パラメータ | 開発 | 本番 | 説明 |
|-----------|------|------|------|
| `pool_size` | 5 | 20 | 常時保持する接続数 |
| `max_overflow` | 10 | 30 | 追加で作成可能な接続数 |
| `pool_timeout` | 30 | 10 | 接続取得タイムアウト(秒) |
| `pool_recycle` | 3600 | 1800 | 接続リサイクル間隔(秒) |
| `pool_pre_ping` | True | True | 使用前にヘルスチェック |

```python
engine = create_async_engine(
    url,
    pool_size=20,
    max_overflow=30,
    pool_timeout=10,
    pool_recycle=1800,
    pool_pre_ping=True,
)
```

---

## 9. チェックリスト

- [ ] `expire_on_commit=False` を設定（セッション外でのアクセス許可）
- [ ] `autoflush=False` を設定（明示的フラッシュ）
- [ ] N+1対策に `selectinload` を使用
- [ ] タイムスタンプは `DateTime(timezone=True)` + `utc_now()`
- [ ] トランザクションはコンテキストマネージャで管理
- [ ] テストは `:memory:` SQLiteを使用
- [ ] Alembic でマイグレーション管理
