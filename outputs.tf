output "redshift_cluster_dns" {
  description = "The DNS name of the cluster of the redshift cluster"
  value       = aws_redshift_cluster.default.dns_name
}

output "redshift_role_arn" {
  description = "Amazon Resource Name (ARN) of redshift role"
  value       = aws_iam_role.redshift_role.arn
}
