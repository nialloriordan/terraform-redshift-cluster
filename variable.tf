# Variable declarations

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "aws_profile" {
  description = "AWS profile"
  type        = string
  default     = "default"
}

variable "vpc_cidr" {
  description = "Primary CIDR block for your VPC"
  type        = string
}

variable "rs_cluster_identifier" {
  description = "Identifier for redshift cluster"
  type        = string
  default     = "sample-cluster"
}

variable "rs_database_name" {
  description = "Database name for redshift cluster"
  type        = string
  default     = "samplecluster"
}

variable "rs_master_username" {
  description = "Username for redshift"
  type        = string
  sensitive   = true
}

variable "rs_master_password" {
  description = "Password for redshift"
  type        = string
  sensitive   = true
}

variable "rs_nodetype" {
  description = "Redshift node type"
  type        = string
}

variable "rs_port" {
  description = "Redshift database port"
  type        = number
  default     = 5439
}

variable "rs_number_of_nodes" {
  description = "Redshift number of nodes"
  type        = number
  default     = 1
}

variable "rs_publicly_accessible" {
  description = "Redshift cluster can be accessed from a public network "
  type        = bool
  default     = false
}

variable "ip_permission_group_map" {
  description = "Permission group for whitelisted ip, maps ip to permission group"
  type        = map(string)
}


