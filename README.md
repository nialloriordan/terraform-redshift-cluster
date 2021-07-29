# Redshift Cluster via Terraform

<details open>
    <summary>Table of Contents</summary>

- [Redshift Cluster via Terraform](#redshift-cluster-via-terraform)
  - [Overview](#overview)
    - [Terraform](#terraform)
      - [Quick Start](#quick-start)
    - [Boto3](#boto3)
  - [Architecture](#architecture)
  - [Structure](#structure)

</details>

## Overview

The purpose of this repo is to provide an easy method to create, update and destroy redshift clusters via Terraform.

The redshift cluster will also be able to access AWS S3 buckets.

### Terraform

#### Quick Start

<details open>
    <summary>Show/Hide Details</summary>

Ensure you have terraform cli installed and setup for local development. More information [here](https://learn.hashicorp.com/tutorials/terraform/install-cli)

Rename [terraform.tfvars.example](terraform.tfvars.example) as `terraform.tfvars`. Update as appropriate as this will contain the value for all relevant variables.

Run `terraform init` to initialise the terraform directory.

Run `terraform plan` to view the execution plan.

Run `terraform apply` to create the redshift cluster. Make sure to enter yes to confirm the execution.

Finally to delete the cluster run `terraform destroy`. Make sure to enter yes to confim the deletion and to destroy any other related objects.

</details>

### Boto3

<details>
    <summary>Show/Hide Details</summary>

For reference I have provided [python scripts](scripts/) to create a redshift cluster via boto3.

In your environment of choice install the following packages using `python 3.6.10`:
- `boto3==1.18.9`
- `psycopg2==2.9.1`

Rename [dwh.cfg.example](scripts/dwh.cfg.example) as `dwh.cfg`. Update as appropriate as this will contain the value for all relevant variables.

Within the [scripts/](scripts/) folder run: `python create_redshift_cluster False` to create a redshift cluster. The first argument passed referes to an option to delete the redshift cluster.

Finally to delete the cluster run `python create_redshift_cluster True` to delete the redshift cluster.

</details>

## Architecture

[Terraform](https://www.terraform.io/) is an IaC tool that allows engineers / developers to build, change and destroy infrastructure conveniently and efficiently.

[Amazon Redshift](https://aws.amazon.com/redshift/) is a column oriented data warehouse with a Postgres compatible querying layer. With Redshift it is possible to scale from 1 to N clusters depending on your storage and query performance needs.

## Structure

<details>
    <summary>Show/Hide Details</summary>

- [main.tf](main.tf): AWS resources to be created by Terraform
- [outputs.tf](outputs.tf): output values once Terraform has created all necessary resources
- [scripts/](scripts/): python scripts to crreate redshift cluster via boto3
  - [create_redshift_cluster.py](scripts/create_redshift_cluster.py): create redshift cluster via boto3
  - [dwh.cfg.example](dwh.cfg.example): example config to create redshift cluster via boto3
- [terraform.tfstate](terraform.tfstate): state file to keep track of resources created by Terraform configuration
- [terraform.tfvars.example](terraform.tfvars.example): value of all input variables
- [variable.tf](variable.tf): holds description and default for all input varaibles

</details>