# Terraform IaC ガイド

## 概要

AWS インフラストラクチャを Terraform で管理するためのテンプレートです。

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                           AWS Cloud                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                         VPC                                │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │                  Public Subnets                      │  │  │
│  │  │   ┌─────────┐  ┌─────────┐  ┌─────────┐            │  │  │
│  │  │   │ NAT GW  │  │ NAT GW  │  │ NAT GW  │            │  │  │
│  │  │   │  (AZ-a) │  │  (AZ-c) │  │  (AZ-d) │            │  │  │
│  │  │   └─────────┘  └─────────┘  └─────────┘            │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │                 Private Subnets                      │  │  │
│  │  │   ┌─────────────────────────────────────────────┐   │  │  │
│  │  │   │              EKS Cluster                     │   │  │  │
│  │  │   │  ┌───────┐  ┌───────┐  ┌───────┐           │   │  │  │
│  │  │   │  │ Node  │  │ Node  │  │ Node  │           │   │  │  │
│  │  │   │  │  (a)  │  │  (c)  │  │  (d)  │           │   │  │  │
│  │  │   │  └───────┘  └───────┘  └───────┘           │   │  │  │
│  │  │   └─────────────────────────────────────────────┘   │  │  │
│  │  │   ┌───────────────┐  ┌───────────────┐             │  │  │
│  │  │   │  RDS (Multi-  │  │  ElastiCache  │             │  │  │
│  │  │   │   AZ/HA)      │  │   (Redis)     │             │  │  │
│  │  │   └───────────────┘  └───────────────┘             │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────┐  ┌───────────────────┐                   │
│  │  Secrets Manager  │  │   CloudWatch      │                   │
│  └───────────────────┘  └───────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

## クイックスタート

### 1. 前提条件

```bash
# Terraform インストール
brew install terraform

# AWS CLI 設定
aws configure
```

### 2. テンプレートをコピー

```bash
mkdir -p infrastructure/terraform
cp sdd-templates/config/terraform/*.tf infrastructure/terraform/
```

### 3. 環境別設定ファイルを作成

```bash
# development.tfvars
cat > infrastructure/terraform/development.tfvars << 'EOF'
project_name    = "web-edi"
environment     = "development"
aws_region      = "ap-northeast-1"

# EKS
eks_node_instance_types = ["t3.medium"]
eks_node_min_size       = 1
eks_node_max_size       = 3
eks_node_desired_size   = 2

# RDS
db_instance_class        = "db.t3.micro"
db_allocated_storage     = 20
db_max_allocated_storage = 50

# Redis
redis_node_type = "cache.t3.micro"
EOF
```

### 4. 初期化とデプロイ

```bash
cd infrastructure/terraform

# 初期化
terraform init

# プラン確認
terraform plan -var-file=development.tfvars

# 適用
terraform apply -var-file=development.tfvars
```

## ディレクトリ構造

```
infrastructure/
└── terraform/
    ├── main.tf           # メイン設定
    ├── variables.tf      # 変数定義
    ├── outputs.tf        # 出力定義
    ├── development.tfvars  # 開発環境
    ├── staging.tfvars      # ステージング
    └── production.tfvars   # 本番環境
```

## 環境別設定

### Development

```hcl
# development.tfvars
environment = "development"

# コスト最適化
eks_node_instance_types = ["t3.medium"]
eks_node_min_size       = 1
eks_node_max_size       = 3
db_instance_class       = "db.t3.micro"
redis_node_type         = "cache.t3.micro"
```

### Production

```hcl
# production.tfvars
environment = "production"

# 高可用性
eks_node_instance_types = ["m5.large", "m5.xlarge"]
eks_node_min_size       = 3
eks_node_max_size       = 10
db_instance_class       = "db.r6g.large"
redis_node_type         = "cache.r6g.large"
```

## State 管理

### S3 Backend 設定

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "web-edi/terraform.tfstate"
    region         = "ap-northeast-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### S3 バケット作成

```bash
# State バケット作成
aws s3api create-bucket \
  --bucket your-terraform-state-bucket \
  --region ap-northeast-1 \
  --create-bucket-configuration LocationConstraint=ap-northeast-1

# バージョニング有効化
aws s3api put-bucket-versioning \
  --bucket your-terraform-state-bucket \
  --versioning-configuration Status=Enabled

# ロックテーブル作成
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## コスト見積もり

| 環境 | EKS | RDS | Redis | 月額概算 |
|------|-----|-----|-------|---------|
| Dev | t3.medium x2 | db.t3.micro | cache.t3.micro | ~$150 |
| Staging | t3.large x2 | db.t3.small | cache.t3.small | ~$250 |
| Prod | m5.large x3 | db.r6g.large (Multi-AZ) | cache.r6g.large | ~$800+ |

## CI/CD 統合

### GitHub Actions

```yaml
name: Terraform

on:
  push:
    branches: [main]
    paths:
      - 'infrastructure/terraform/**'
  pull_request:
    paths:
      - 'infrastructure/terraform/**'

jobs:
  terraform:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: infrastructure/terraform

    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.5.0

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        run: terraform plan -var-file=${{ github.event_name == 'push' && 'production' || 'staging' }}.tfvars -no-color
        continue-on-error: true

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: terraform apply -var-file=production.tfvars -auto-approve
```

## セキュリティベストプラクティス

### 1. IAM 最小権限

```hcl
# EKS ノード用 IAM ロール（最小権限）
resource "aws_iam_role_policy" "eks_node_minimal" {
  name = "eks-node-minimal"
  role = module.eks.eks_managed_node_groups.default.iam_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ]
        Resource = "*"
      }
    ]
  })
}
```

### 2. 暗号化

- RDS: 保存時暗号化（AWS KMS）
- ElastiCache: 転送中暗号化
- Secrets Manager: 自動ローテーション

### 3. ネットワーク分離

- Private Subnet にデータベース配置
- Security Group で最小限の通信許可
- VPC Endpoints でAWSサービスへのプライベートアクセス

## トラブルシューティング

### EKS 接続エラー

```bash
# kubeconfig 更新
aws eks update-kubeconfig --region ap-northeast-1 --name web-edi-production-eks

# クラスター状態確認
kubectl get nodes
kubectl get pods -A
```

### RDS 接続エラー

```bash
# Security Group 確認
aws ec2 describe-security-groups --group-ids <sg-id>

# エンドポイント疎通確認
nc -zv <rds-endpoint> 5432
```

## 関連ドキュメント

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [terraform-aws-modules](https://registry.terraform.io/namespaces/terraform-aws-modules)
- [AWS Well-Architected](https://aws.amazon.com/architecture/well-architected/)
