# Datetime/Timezone パターン (CRITICAL)

> **このガイドラインは必須です。datetime.utcnow() は非推奨であり、使用禁止です。**

---

## 1. 原則: UTC-First Design

すべての datetime は **UTC で保存**し、**表示時にローカルタイムゾーンに変換**する。

```
[User Input (Local)] → [Convert to UTC] → [Store in DB] → [Retrieve as UTC] → [Convert to Local] → [Display]
```

---

## 2. Python datetime の正しい使い方

### 2.1 禁止パターン (INVIOLABLE)

```python
# ❌ 禁止: naive datetime (タイムゾーン情報なし)
from datetime import datetime
now = datetime.now()           # タイムゾーンなし
utc_now = datetime.utcnow()    # Python 3.12で非推奨、将来削除予定

# ❌ 禁止: utcnow() は非推奨
# DeprecationWarning: datetime.datetime.utcnow() is deprecated
```

### 2.2 推奨パターン

```python
from datetime import UTC, datetime, timezone

# ✅ 正解: timezone-aware datetime
def utc_now() -> datetime:
    """現在のUTC時刻を取得（タイムゾーン付き）"""
    return datetime.now(UTC)

# ✅ 正解: 明示的なタイムゾーン指定
now_utc = datetime.now(UTC)
now_utc = datetime.now(timezone.utc)  # 同等

# ✅ 正解: タイムスタンプからの変換
from_timestamp = datetime.fromtimestamp(1704067200, tz=UTC)

# ✅ 正解: ISO形式文字列のパース
parsed = datetime.fromisoformat("2024-01-01T00:00:00+00:00")
```

---

## 3. SQLAlchemy モデルでの使用

### 3.1 禁止パターン

```python
from datetime import datetime
from sqlalchemy.orm import mapped_column

# ❌ 禁止: utcnow を直接参照
class Order(Base):
    created_at = mapped_column(DateTime, default=datetime.utcnow)  # 非推奨警告
    updated_at = mapped_column(DateTime, onupdate=datetime.utcnow)  # 非推奨警告
```

### 3.2 推奨パターン

```python
from datetime import UTC, datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

def utc_now() -> datetime:
    """UTC現在時刻を返すヘルパー関数"""
    return datetime.now(UTC)

class Base(DeclarativeBase):
    pass

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(primary_key=True)

    # ✅ 正解: ヘルパー関数を使用
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
```

### 3.3 データベースカラムの設定

```python
from sqlalchemy import DateTime

# ✅ 正解: timezone=True でタイムゾーン付きカラム
created_at = mapped_column(DateTime(timezone=True), default=utc_now)

# PostgreSQL: TIMESTAMP WITH TIME ZONE
# SQLite: TEXT (ISO形式文字列)
# MySQL: DATETIME(6) + アプリ側でTZ管理
```

---

## 4. dataclass / Pydantic での使用

### 4.1 dataclass

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime

def utc_now() -> datetime:
    return datetime.now(UTC)

@dataclass
class Order:
    id: str
    # ✅ 正解: default_factory でヘルパー関数を使用
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
```

### 4.2 Pydantic

```python
from datetime import UTC, datetime
from pydantic import BaseModel, Field

class Order(BaseModel):
    id: str
    # ✅ 正解: default_factory を使用
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()  # ISO 8601形式でシリアライズ
        }
```

---

## 5. API レスポンスでの日時フォーマット

### 5.1 JSON シリアライズ

```python
from datetime import UTC, datetime
import json

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # ✅ ISO 8601形式 + タイムゾーン
            return obj.isoformat()
        return super().default(obj)

# 出力例: "2024-01-01T12:00:00+00:00"
```

### 5.2 FastAPI レスポンス

```python
from fastapi import FastAPI
from datetime import UTC, datetime
from pydantic import BaseModel

class OrderResponse(BaseModel):
    id: str
    created_at: datetime  # 自動的にISO形式でシリアライズ

# レスポンス例:
# {"id": "abc123", "created_at": "2024-01-01T12:00:00+00:00"}
```

---

## 6. テストでの日時固定

### 6.1 freezegun を使用

```python
from datetime import UTC, datetime
import pytest
from freezegun import freeze_time

@freeze_time("2024-01-01 12:00:00", tz_offset=0)
def test_order_created_at():
    order = create_order()
    expected = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert order.created_at == expected
```

### 6.2 モック使用

```python
from datetime import UTC, datetime
from unittest.mock import patch

def test_order_timestamp():
    fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    with patch('myapp.models.utc_now', return_value=fixed_time):
        order = create_order()
        assert order.created_at == fixed_time
```

---

## 7. マイグレーションガイド

既存の `datetime.utcnow()` を使用しているコードを修正する手順:

### Step 1: ヘルパー関数の追加

```python
# src/utils/datetime.py
from datetime import UTC, datetime

def utc_now() -> datetime:
    """UTC現在時刻を返す（タイムゾーン付き）"""
    return datetime.now(UTC)
```

### Step 2: インポートの置換

```bash
# 検索: datetime.utcnow
grep -r "datetime.utcnow" src/

# 置換パターン:
# datetime.utcnow() → utc_now()
# datetime.utcnow → utc_now (default引数の場合)
```

### Step 3: SQLAlchemy モデルの修正

```python
# Before
created_at = mapped_column(DateTime, default=datetime.utcnow)

# After
created_at = mapped_column(DateTime(timezone=True), default=utc_now)
```

### Step 4: テスト実行

```bash
# 警告を表示してテスト
python -m pytest -W default::DeprecationWarning

# 期待結果: datetime.utcnow() 関連の警告が0件
```

---

## 8. CI/CD での検出

### pyproject.toml 設定

```toml
[tool.pytest.ini_options]
filterwarnings = [
    "error::DeprecationWarning",  # 非推奨警告をエラーとして扱う
]
```

### ESLint (TypeScript) 類似ルール

```javascript
// カスタムルールで new Date() の使用を検出
// 推奨: dayjs.utc() または date-fns の formatISO
```

---

## 9. チェックリスト

- [ ] `datetime.utcnow()` を使用していない
- [ ] `datetime.now()` を引数なしで使用していない
- [ ] すべての datetime カラムに `timezone=True` を設定
- [ ] APIレスポンスは ISO 8601 形式 (タイムゾーン付き)
- [ ] テストで日時を固定している
- [ ] CI で DeprecationWarning を検出

---

## 10. 参考資料

- [PEP 615 – Support for the IANA Time Zone Database](https://peps.python.org/pep-0615/)
- [Python 3.12 What's New - Deprecations](https://docs.python.org/3.12/whatsnew/3.12.html)
- [SQLAlchemy DateTime with Timezone](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.DateTime)
