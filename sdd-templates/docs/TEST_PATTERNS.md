# Test Patterns - SDD Template

Version: 5.3.3-tecnos-stride

実践で検証済みのテストパターン集。カバレッジ改善と品質向上に活用。

---

## 目次

1. [認証テストパターン](#1-認証テストパターン)
2. [CRUDテストパターン](#2-crudテストパターン)
3. [ワークフローテストパターン](#3-ワークフローテストパターン)
4. [エラーハンドリングパターン](#4-エラーハンドリングパターン)
5. [フィルタリング・ページネーションパターン](#5-フィルタリングページネーションパターン)
6. [契約テストパターン](#6-契約テストパターン)
7. [カバレッジ改善パターン](#7-カバレッジ改善パターン)

---

## 1. 認証テストパターン

### 1.1 ログイン成功/失敗

```python
class TestLogin:
    """認証テスト"""

    def test_login_success(self, client, buyer_user):
        """正常ログイン"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": buyer_user["username"],
                "password": buyer_user["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["role"] == "buyer"

    def test_login_invalid_password(self, client, buyer_user):
        """パスワード誤り"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": buyer_user["username"],
                "password": "wrong_password",
            },
        )
        assert response.status_code == 401

    def test_login_user_not_found(self, client):
        """存在しないユーザー"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "any"},
        )
        assert response.status_code == 401
```

### 1.2 認可テスト（ロールベース）

```python
class TestAuthorization:
    """認可テスト"""

    def test_buyer_cannot_access_supplier_endpoint(self, client, buyer_session):
        """買い手はサプライヤー専用エンドポイントにアクセス不可"""
        response = client.post("/api/v1/orders/{order_id}/shipment", json={...})
        assert response.status_code == 403

    def test_admin_only_endpoint(self, client, buyer_session):
        """管理者専用エンドポイント"""
        response = client.get("/api/v1/audit-logs")
        assert response.status_code == 403

    def test_admin_can_access(self, client, admin_session):
        """管理者はアクセス可能"""
        response = client.get("/api/v1/audit-logs")
        assert response.status_code == 200
```

---

## 2. CRUDテストパターン

### 2.1 作成テスト

```python
class TestCreate:
    """作成テスト"""

    def test_create_success(self, client, buyer_session, valid_data):
        """正常作成"""
        response = client.post(
            "/api/v1/resource",
            json=valid_data,
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        assert response.status_code == 201
        assert "id" in response.json()

    def test_create_idempotency(self, client, buyer_session, valid_data):
        """冪等性確認"""
        key = str(uuid.uuid4())
        r1 = client.post("/api/v1/resource", json=valid_data, headers={"Idempotency-Key": key})
        r2 = client.post("/api/v1/resource", json=valid_data, headers={"Idempotency-Key": key})
        assert r1.json()["id"] == r2.json()["id"]

    def test_create_validation_error(self, client, buyer_session):
        """バリデーションエラー"""
        response = client.post(
            "/api/v1/resource",
            json={"invalid": "data"},
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        assert response.status_code == 422
```

### 2.2 取得テスト

```python
class TestGet:
    """取得テスト"""

    def test_get_success(self, client, buyer_session, created_resource):
        """正常取得"""
        response = client.get(f"/api/v1/resource/{created_resource['id']}")
        assert response.status_code == 200

    def test_get_not_found(self, client, buyer_session):
        """存在しないリソース"""
        response = client.get(f"/api/v1/resource/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_get_other_users_resource(self, client, buyer_session, other_user_resource):
        """他ユーザーのリソースアクセス不可"""
        response = client.get(f"/api/v1/resource/{other_user_resource['id']}")
        assert response.status_code == 403
```

---

## 3. ワークフローテストパターン

### 3.1 完全ワークフロー

```python
class TestFullWorkflow:
    """完全ワークフローテスト（作成→確認→出荷→受領）"""

    def test_complete_workflow(self, client, buyer_user, supplier_user, supplier_company):
        """正常ワークフロー完走"""
        # Step 1: 買い手ログイン＆注文作成
        client.post("/api/v1/auth/login", json={
            "username": buyer_user["username"],
            "password": buyer_user["password"],
        })
        create_resp = client.post(
            "/api/v1/orders",
            json={
                "supplier_id": str(supplier_company.id),
                "items": [{"product_code": "P001", "quantity": 10, "unit": "pcs"}],
                "delivery_date": str(date.today() + timedelta(days=7)),
            },
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        order_id = create_resp.json()["order_id"]

        # Step 2: サプライヤーログイン＆確認
        client.post("/api/v1/auth/login", json={
            "username": supplier_user["username"],
            "password": supplier_user["password"],
        })
        client.post(f"/api/v1/orders/{order_id}/confirmation", json={
            "status": "accepted",
            "notes": "Confirmed",
        })

        # Step 3: 出荷
        client.post(f"/api/v1/orders/{order_id}/shipment", json={
            "shipment_date": str(date.today()),
            "carrier": "DHL",
            "tracking_number": "TRACK001",
        })

        # Step 4: 買い手ログイン＆受領
        client.post("/api/v1/auth/login", json={
            "username": buyer_user["username"],
            "password": buyer_user["password"],
        })
        client.post(f"/api/v1/orders/{order_id}/receipt", json={
            "receipt_date": str(date.today()),
            "received_quantity": 10,
        })

        # Step 5: 履歴確認
        detail = client.get(f"/api/v1/transactions/{order_id}").json()
        assert detail["order"]["confirmation"] is not None
        assert detail["order"]["shipment"] is not None
        assert detail["order"]["receipt"] is not None
        assert len(detail["history"]) >= 4
```

### 3.2 状態遷移エラーテスト

```python
class TestStateTransitionErrors:
    """不正な状態遷移テスト"""

    def test_cannot_ship_before_accept(self, client, supplier_session, created_order):
        """承認前に出荷不可"""
        response = client.post(
            f"/api/v1/orders/{created_order['order_id']}/shipment",
            json={"shipment_date": str(date.today()), "carrier": "DHL"},
        )
        assert response.status_code == 400

    def test_cannot_receive_before_ship(self, client, buyer_session, accepted_order):
        """出荷前に受領不可"""
        response = client.post(
            f"/api/v1/orders/{accepted_order['order_id']}/receipt",
            json={"receipt_date": str(date.today()), "received_quantity": 10},
        )
        assert response.status_code == 400

    def test_cannot_confirm_twice(self, client, supplier_session, accepted_order):
        """二重確認不可"""
        response = client.post(
            f"/api/v1/orders/{accepted_order['order_id']}/confirmation",
            json={"status": "accepted"},
        )
        assert response.status_code == 400
```

---

## 4. エラーハンドリングパターン

### 4.1 標準エラーレスポンス

```python
class TestErrorResponses:
    """エラーレスポンステスト"""

    def test_401_unauthorized(self, client):
        """認証なし"""
        response = client.get("/api/v1/orders")
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_403_forbidden(self, client, buyer_session, supplier_only_endpoint):
        """権限なし"""
        response = client.post(supplier_only_endpoint)
        assert response.status_code == 403

    def test_404_not_found(self, client, buyer_session):
        """リソースなし"""
        response = client.get(f"/api/v1/orders/{uuid.uuid4()}")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_422_validation_error(self, client, buyer_session):
        """バリデーションエラー"""
        response = client.post("/api/v1/orders", json={})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)  # Pydantic error format
```

---

## 5. フィルタリング・ページネーションパターン

### 5.1 フィルタリング

```python
class TestFiltering:
    """フィルタリングテスト"""

    def test_filter_by_status(self, client, buyer_session, orders_with_various_status):
        """ステータスフィルタ"""
        response = client.get("/api/v1/orders?status=ordered")
        assert response.status_code == 200
        for item in response.json()["items"]:
            assert item["status"] == "ordered"

    def test_filter_by_date_range(self, client, buyer_session, orders_on_various_dates):
        """日付範囲フィルタ"""
        today = date.today()
        response = client.get(
            f"/api/v1/orders?date_from={today - timedelta(days=7)}&date_to={today}"
        )
        assert response.status_code == 200

    def test_filter_no_results(self, client, buyer_session):
        """結果なしフィルタ"""
        response = client.get("/api/v1/orders?status=nonexistent")
        assert response.status_code == 200
        assert response.json()["items"] == []
```

### 5.2 ページネーション

```python
class TestPagination:
    """ページネーションテスト"""

    def test_pagination_first_page(self, client, buyer_session, many_orders):
        """1ページ目"""
        response = client.get("/api/v1/orders?page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10
        assert data["page"] == 1
        assert data["size"] == 10
        assert "total" in data

    def test_pagination_second_page(self, client, buyer_session, many_orders):
        """2ページ目"""
        response = client.get("/api/v1/orders?page=2&size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2

    def test_pagination_beyond_total(self, client, buyer_session):
        """範囲外ページ"""
        response = client.get("/api/v1/orders?page=9999&size=10")
        assert response.status_code == 200
        assert response.json()["items"] == []
```

---

## 6. 契約テストパターン

### 6.1 OpenAPIスキーマ検証

```python
class TestApiContract:
    """API契約テスト"""

    def test_response_schema(self, client, buyer_session, created_order):
        """レスポンススキーマ検証"""
        response = client.get(f"/api/v1/orders/{created_order['order_id']}")
        data = response.json()

        # 必須フィールドの存在確認
        required_fields = ["order_id", "status", "items", "created_at"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # 型検証
        assert isinstance(data["order_id"], str)
        assert isinstance(data["items"], list)
        assert isinstance(data["status"], str)

    def test_error_response_schema(self, client, buyer_session):
        """エラーレスポンススキーマ"""
        response = client.get(f"/api/v1/orders/{uuid.uuid4()}")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
```

### 6.2 Correlation-ID / Idempotency

```python
class TestCorrelationId:
    """Correlation-IDテスト"""

    def test_correlation_id_echo(self, client, buyer_session):
        """送信したIDがエコーされる"""
        correlation_id = f"test-{uuid.uuid4()}"
        response = client.get(
            "/api/v1/orders",
            headers={"X-Correlation-ID": correlation_id},
        )
        assert response.headers.get("X-Correlation-ID") == correlation_id

    def test_correlation_id_generated(self, client, buyer_session):
        """未指定時は自動生成"""
        response = client.get("/api/v1/orders")
        assert "X-Correlation-ID" in response.headers
```

---

## 7. カバレッジ改善パターン

### 7.1 低カバレッジモジュール特定

```bash
# 80%未満のモジュールをリスト
python -m pytest --cov=src --cov-report=term-missing 2>&1 | \
  grep -E "^src/.*\s+\d+\s+\d+\s+\d+\s+\d+\s+[0-7][0-9]%" | \
  sort -t'%' -k1 -n
```

### 7.2 未テストコードの分析

**優先度判定基準**:

| 優先度 | コード種別 | 理由 |
|--------|-----------|------|
| 高 | ビジネスロジック | バグが致命的 |
| 高 | 認証/認可 | セキュリティリスク |
| 中 | APIエンドポイント | ユーザー影響 |
| 中 | バリデーション | データ整合性 |
| 低 | リポジトリ層 | 統合テストでカバー |
| 除外 | HTMLレンダリング | E2Eでカバー |

### 7.3 エラーパス追加パターン

```python
# 典型的な未テストエラーパス
class TestErrorPaths:
    """エラーパステスト（カバレッジ改善用）"""

    def test_resource_not_found(self, client, session):
        """存在しないリソース"""
        response = client.get(f"/api/v1/resource/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_invalid_state_transition(self, client, session, resource_in_wrong_state):
        """不正な状態遷移"""
        response = client.post(f"/api/v1/resource/{resource_id}/invalid_action")
        assert response.status_code == 400

    def test_permission_denied(self, client, other_user_session, resource):
        """権限なし"""
        response = client.get(f"/api/v1/resource/{resource['id']}")
        assert response.status_code == 403

    def test_already_exists(self, client, session, existing_resource):
        """重複作成"""
        response = client.post("/api/v1/resource", json=existing_resource)
        assert response.status_code == 409  # or 400
```

---

## 関連ドキュメント

- `agent_docs/testing.md` - テスト実行ガイド
- `config/testing/python/conftest.py.template` - Pythonフィクスチャテンプレート
- `config/testing/python/test_api.py.template` - APIテストテンプレート
- `docs/CI_CD_INTEGRATION.md` - CI/CDパイプライン設定
