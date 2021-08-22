terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.55.0"
    }
  }

  required_version = ">=1.0.4"
}
provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

resource "aws_iam_role" "redshift_role" {
  name = "redshift_role"
  assume_role_policy = jsonencode({
    "Statement" : [{
      "Action" : "sts:AssumeRole",
      "Effect" : "Allow",
      "Principal" : { "Service" : "redshift.amazonaws.com" }
    }],
    "Version" : "2012-10-17"
  })
}

resource "aws_iam_role_policy_attachment" "attach_s3_redshift_role" {
  role       = aws_iam_role.redshift_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_redshift_cluster" "default" {
  cluster_identifier  = var.rs_cluster_identifier
  database_name       = var.rs_database_name
  master_username     = var.rs_master_username
  master_password     = var.rs_master_password
  node_type           = var.rs_nodetype
  number_of_nodes     = var.rs_number_of_nodes
  cluster_type        = var.rs_number_of_nodes > 1 ? "multi-node" : "single-node"
  skip_final_snapshot = true
  iam_roles           = [aws_iam_role.redshift_role.arn]
  publicly_accessible = var.rs_publicly_accessible
  port                = var.rs_port
}

resource "aws_vpc" "redshift_vpc" {
  cidr_block       = var.vpc_cidr
  instance_tenancy = "default"
}

resource "aws_default_security_group" "redshift_security_group" {
  vpc_id = aws_vpc.redshift_vpc.id
  ingress {
    from_port   = var.rs_port
    to_port     = var.rs_port
    protocol    = "tcp"
    cidr_blocks = [for ip, pem in var.ip_permission_group_map : "${ip}/${pem}"]
  }
}
