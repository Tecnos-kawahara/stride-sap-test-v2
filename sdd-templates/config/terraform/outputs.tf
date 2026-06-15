# =============================================================================
# Terraform Outputs
# Infrastructure values for application configuration
# =============================================================================

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

# -----------------------------------------------------------------------------
# EKS
# -----------------------------------------------------------------------------

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_arn" {
  description = "EKS cluster ARN"
  value       = module.eks.cluster_arn
}

output "eks_cluster_certificate_authority_data" {
  description = "EKS cluster CA certificate"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "eks_kubeconfig_command" {
  description = "Command to update kubeconfig"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

# -----------------------------------------------------------------------------
# RDS
# -----------------------------------------------------------------------------

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_instance_endpoint
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.rds.db_instance_port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = module.rds.db_instance_name
}

# -----------------------------------------------------------------------------
# ElastiCache
# -----------------------------------------------------------------------------

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = module.elasticache.cluster_cache_nodes[0].address
}

output "redis_port" {
  description = "Redis port"
  value       = 6379
}

# -----------------------------------------------------------------------------
# Secrets Manager
# -----------------------------------------------------------------------------

output "secrets_manager_arn" {
  description = "Secrets Manager secret ARN"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

# -----------------------------------------------------------------------------
# Connection Strings (for reference only - use Secrets Manager in practice)
# -----------------------------------------------------------------------------

output "database_url" {
  description = "Database connection URL (retrieve from Secrets Manager)"
  value       = "postgresql+asyncpg://${var.db_username}:****@${module.rds.db_instance_endpoint}/${var.db_name}"
  sensitive   = false
}

output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://${module.elasticache.cluster_cache_nodes[0].address}:6379/0"
}
