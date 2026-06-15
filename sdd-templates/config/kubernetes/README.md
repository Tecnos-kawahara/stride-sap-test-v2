# Kubernetes マニフェストガイド

## 概要

本番環境向けのKubernetesマニフェストテンプレートです。

## ファイル構成

| ファイル | 説明 |
|---------|------|
| `deployment.yaml` | アプリケーションのデプロイメント |
| `service.yaml` | クラスタ内サービス公開 |
| `ingress.yaml` | 外部アクセス（TLS終端） |
| `hpa.yaml` | 水平ポッドオートスケーラー |
| `configmap.yaml` | 設定・シークレット |
| `kustomization.yaml` | Kustomize設定 |

## クイックスタート

### 1. Kustomize で環境別設定

```bash
# ディレクトリ構造
k8s/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── configmap.yaml
│   └── kustomization.yaml
└── overlays/
    ├── development/
    │   └── kustomization.yaml
    ├── staging/
    │   └── kustomization.yaml
    └── production/
        └── kustomization.yaml
```

### 2. テンプレートをコピー

```bash
mkdir -p k8s/base k8s/overlays/{development,staging,production}
cp sdd-templates/config/kubernetes/*.yaml k8s/base/
```

### 3. 変数を置換

```bash
# 環境変数を設定
export APP_NAME=web-edi
export NAMESPACE=web-edi
export APP_VERSION=1.0.0
export ENVIRONMENT=production
export DOMAIN=web-edi.example.com

# 変数を置換（envsubst使用）
for file in k8s/base/*.yaml; do
  envsubst < "$file" > "$file.tmp" && mv "$file.tmp" "$file"
done
```

### 4. デプロイ

```bash
# Kustomize でデプロイ
kubectl apply -k k8s/overlays/production/

# または直接適用
kubectl apply -f k8s/base/
```

## Kustomization 設定

### base/kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: web-edi

resources:
  - deployment.yaml
  - service.yaml
  - ingress.yaml
  - hpa.yaml
  - configmap.yaml

commonLabels:
  app.kubernetes.io/name: web-edi
  app.kubernetes.io/managed-by: kustomize
```

### overlays/production/kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: web-edi-production

resources:
  - ../../base

namePrefix: prod-

commonLabels:
  environment: production

patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 3
    target:
      kind: Deployment
      name: web-edi

  - patch: |-
      - op: replace
        path: /spec/minReplicas
        value: 3
      - op: replace
        path: /spec/maxReplicas
        value: 20
    target:
      kind: HorizontalPodAutoscaler
      name: web-edi

configMapGenerator:
  - name: web-edi-config
    behavior: merge
    literals:
      - APP_ENV=production
      - APP_LOG_LEVEL=WARNING

secretGenerator:
  - name: web-edi-secrets
    type: Opaque
    files:
      - secrets/database-url
      - secrets/secret-key
```

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Ingress Controller                           │
│                    (NGINX / ALB)                                │
│                    - TLS Termination                            │
│                    - Rate Limiting                              │
│                    - Security Headers                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service (ClusterIP)                        │
│                      web-edi:80                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Deployment                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Pod 1     │  │    Pod 2     │  │    Pod 3     │          │
│  │  (app:8000)  │  │  (app:8000)  │  │  (app:8000)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                         ▲                                        │
│                         │ HPA (Auto-scale 2-10)                 │
└─────────────────────────┼───────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │PostgreSQL│     │  Redis   │     │OTel Coll │
  │ (RDS)    │     │(Elastic) │     │          │
  └──────────┘     └──────────┘     └──────────┘
```

## セキュリティ設定

### Pod Security Standards

```yaml
# Namespace に適用
apiVersion: v1
kind: Namespace
metadata:
  name: web-edi
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Network Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-edi-network-policy
  namespace: web-edi
spec:
  podSelector:
    matchLabels:
      app: web-edi
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - port: 8000
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: database
      ports:
        - port: 5432
    - to:
        - namespaceSelector:
            matchLabels:
              name: redis
      ports:
        - port: 6379
```

## リソース見積もり

| 環境 | レプリカ | CPU (req/lim) | Memory (req/lim) |
|------|---------|---------------|------------------|
| Dev | 1 | 100m/250m | 128Mi/256Mi |
| Staging | 2 | 100m/500m | 256Mi/512Mi |
| Prod | 3-10 | 250m/1000m | 512Mi/1Gi |

## トラブルシューティング

### Pod が起動しない

```bash
# Pod 状態確認
kubectl get pods -n web-edi
kubectl describe pod <pod-name> -n web-edi

# ログ確認
kubectl logs <pod-name> -n web-edi

# イベント確認
kubectl get events -n web-edi --sort-by='.lastTimestamp'
```

### Ingress が動作しない

```bash
# Ingress 状態確認
kubectl get ingress -n web-edi
kubectl describe ingress web-edi -n web-edi

# TLS 証明書確認
kubectl get certificate -n web-edi
kubectl describe certificate web-edi-tls -n web-edi
```

### HPA がスケールしない

```bash
# HPA 状態確認
kubectl get hpa -n web-edi
kubectl describe hpa web-edi -n web-edi

# メトリクスサーバー確認
kubectl top pods -n web-edi
```

## CI/CD 統合

### GitHub Actions

```yaml
- name: Deploy to Kubernetes
  run: |
    kubectl apply -k k8s/overlays/${{ env.ENVIRONMENT }}/
    kubectl rollout status deployment/web-edi -n web-edi --timeout=300s
```

### ArgoCD

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-edi
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/web-edi
    targetRevision: main
    path: k8s/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: web-edi
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## 関連ドキュメント

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize](https://kustomize.io/)
- [cert-manager](https://cert-manager.io/docs/)
- [External Secrets Operator](https://external-secrets.io/)
