import boto3
import json
import logging
import configparser
import time
import psycopg2
import sys

# CONFIG
config = configparser.ConfigParser()
config.read_file(open("dwh.cfg"))

KEY = config.get("AWS", "ACCESS_KEY_ID")
SECRET = config.get("AWS", "SECRET_ACCESS_KEY")

DWH_CLUSTER_TYPE = config.get("CLUSTER", "DWH_CLUSTER_TYPE")
DWH_NODE_TYPE = config.get("CLUSTER", "DWH_NODE_TYPE")
REGION = config.get("CLUSTER", "REGION")

DWH_CLUSTER_IDENTIFIER = config.get("CLUSTER", "DWH_CLUSTER_IDENTIFIER")
DWH_DB = config.get("DB", "DB_NAME")
DWH_DB_USER = config.get("DB", "DB_USER")
DWH_DB_PASSWORD = config.get("DB", "DB_PASSWORD")
DWH_PORT = config.get("DB", "DB_PORT")

DWH_IAM_ROLE_NAME = config.get("CLUSTER", "DWH_IAM_ROLE_NAME")

S3_READ_ARN = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"

IP = config.get("IP", "IP_ADDRESS")
PERMISSION_GROUP = config.get("IP", "PERMISSION_GROUP")


def create_resources(aws_options):
    """Create required AWS resources"""

    ec2 = boto3.resource("ec2", **aws_options)
    s3 = boto3.resource("s3", **aws_options)
    iam = boto3.client("iam", **aws_options)
    redshift = boto3.client("redshift", **aws_options)
    return ec2, s3, iam, redshift


def create_iam_role(iam, role_name, s3_policy_arn):
    """Create IAM Roale"""
    # create role for redshift
    try:
        dwhRole = iam.create_role(
            Path="/",
            RoleName=role_name,
            Description="Allows Redshift clusters to call AWS services on your behalf.",
            AssumeRolePolicyDocument=json.dumps(
                {
                    "Statement": [
                        {
                            "Action": "sts:AssumeRole",
                            "Effect": "Allow",
                            "Principal": {"Service": "redshift.amazonaws.com"},
                        }
                    ],
                    "Version": "2012-10-17",
                }
            ),
        )
    except iam.exceptions.EntityAlreadyExistsException as e:
        logging.error(e)

    # attach s3 role policy
    iam.attach_role_policy(RoleName=role_name, PolicyArn=s3_policy_arn)

    # get role ARN
    role_arn = iam.get_role(RoleName=role_name)["Role"]["Arn"]

    return role_arn


def create_redshift_cluster(
    redshift,
    role_arn,
    cluster_type,
    node_type,
    db_name,
    cluster_name,
    db_user,
    db_password,
    public_access=False,
):
    """Create Redshift Cluster"""
    try:
        response = redshift.create_cluster(
            # HW
            ClusterType=cluster_type,
            NodeType=node_type,
            # Identifiers & Credentials
            DBName=db_name,
            ClusterIdentifier=cluster_name,
            MasterUsername=db_user,
            MasterUserPassword=db_password,
            PubliclyAccessible=True,
            # Roles (for s3 access)
            IamRoles=[role_arn],
        )
    except redshift.exceptions.ClusterAlreadyExistsFault as e:
        logging.error(e)


def query_cluster_availability(redshift, cluster_name):
    """Query Redshift cluster"""
    # query the Redshift cluster until available
    timestep = 15
    for _ in range(int(600 / timestep)):
        cluster = redshift.describe_clusters(ClusterIdentifier=DWH_CLUSTER_IDENTIFIER)["Clusters"][
            0
        ]
        cluster_status = cluster["ClusterStatus"]
        if cluster_status == "available":
            break
        logging.info(f'Cluster status is "{cluster_status}". ' f"Retrying in {timestep} seconds.")
        time.sleep(timestep)
    return cluster


def open_tcp_port(ec2, cluster, port, ip, permission_group):
    """Open TCP port"""
    try:
        vpc = ec2.Vpc(id=cluster["VpcId"])
        defaultSg = list(vpc.security_groups.all())[0]
        defaultSg.authorize_ingress(
            GroupName=defaultSg.group_name,
            CidrIp=f"{ip}/{permission_group}",
            IpProtocol="TCP",
            FromPort=int(port),
            ToPort=int(port),
        )
    except Exception as e:
        logging.error(e)


def delete_iam_role(iam, role_name, s3_arn):
    """Delete IAM role"""
    try:
        role_arn = iam.get_role(RoleName=role_name)["Role"]["Arn"]
        iam.detach_role_policy(RoleName=role_name, PolicyArn=s3_arn)
        iam.delete_role(RoleName=role_name)
        logging.info(f"Deleted role {role_name} with {role_arn}")
    except Exception as e:
        logging.error(e)


def delete_redshift_cluster(redshift, cluster_id):
    """Delete Redshift cluster"""
    try:
        redshift.delete_cluster(
            ClusterIdentifier=cluster_id,
            SkipFinalClusterSnapshot=True,
        )
        logging.info(f"Deleted cluster {cluster_id}")
    except Exception as e:
        logging.error(e)


def main(delete=False):
    """Main function"""
    # specify aws options
    options = dict(region_name=REGION, aws_access_key_id=KEY, aws_secret_access_key=SECRET)

    # create resources
    ec2, s3, iam, redshift = create_resources(options)
    if delete == True:
        # delete redshift cluster
        delete_redshift_cluster(redshift, DWH_CLUSTER_IDENTIFIER)
        # delete iam role
        delete_iam_role(iam, DWH_IAM_ROLE_NAME, S3_READ_ARN)
    else:
        # create iam role
        role_arn = create_iam_role(iam, DWH_IAM_ROLE_NAME, S3_READ_ARN)
        # create redshift cluster
        create_redshift_cluster(
            redshift,
            role_arn,
            DWH_CLUSTER_TYPE,
            DWH_NODE_TYPE,
            DWH_DB,
            DWH_CLUSTER_IDENTIFIER,
            DWH_DB_USER,
            DWH_DB_PASSWORD,
        )

        # Query the Redshift cluster after creation until available
        cluster = query_cluster_availability(redshift, DWH_CLUSTER_IDENTIFIER)

        # Open TCP connection upon successful cluster creation
        if cluster:
            cluster_endpoint = cluster["Endpoint"]["Address"]
            logging.info(f"Cluster created at {cluster_endpoint}")
            open_tcp_port(ec2, cluster, DWH_PORT, IP, PERMISSION_GROUP)
        else:
            logging.exception("Could not connect to cluster")
            raise Exception("Could not connect to cluster")

        # test connection to cluster
        conn_string = (
            f"postgresql://{DWH_DB_USER}:{DWH_DB_PASSWORD}@{cluster_endpoint}:{DWH_PORT}/{DWH_DB}"
        )
        conn = psycopg2.connect(conn_string)
        if not conn.closed:
            logging.info(f"Connected: {DWH_DB_USER}@{DWH_DB}")
        else:
            logging.exception("Unable to connect to cluster")
            raise Exception("Connection not valid")

        return cluster_endpoint


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    delete = bool(sys.argv[1])
    logging.info(f"Passed value for delete: {delete}")
    main(delete)
