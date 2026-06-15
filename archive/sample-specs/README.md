# Sample Specs（サンプルスペック）

このディレクトリには、SDD テンプレートの参照用サンプルが格納されています。

## 収録サンプル

| ディレクトリ | 内容 |
|-------------|------|
| `sample_erp_addon/` | ERP アドオン開発の完全なサンプルスペック一式 |
| `FEAT-ERP-OMS/` | ERP OMS（受注管理システム）の実装詳細まで含むサンプル |
| `EPIC-SAMPLE/` | エピック管理のサンプル（PM Dashboard、進捗レポート等） |

## 使い方

新規プロジェクトを始める際の参考にしてください。
実際のプロジェクトでは `stride new-project` コマンドで `specs/` を初期化してください。

```bash
sdd-templates/bin/stride new-project <project_name> --org <your-org>
```
