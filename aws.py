import streamlit as st
import boto3
import json
from botocore.exceptions import ClientError

st.set_page_config(page_title="AWS Config Architecture Scanner", layout="wide")

st.title("AWS Config Architecture Scanner")

st.markdown("""
Enter your AWS IAM Read-Only credentials and region below to fetch the deployed AWS architecture using AWS Config.
""")

access_key = st.text_input("Access Key ID", type="password")
secret_key = st.text_input("Secret Access Key", type="password")
region = st.text_input("AWS Region (e.g., us-east-1)")

resource_types = [
    # Compute
    'AWS::EC2::Instance',
    'AWS::EC2::SecurityGroup',
    'AWS::EC2::Volume',
    'AWS::EC2::VPC',
    'AWS::EC2::Subnet',
    'AWS::EC2::InternetGateway',
    'AWS::EC2::NatGateway',
    'AWS::EC2::RouteTable',
    'AWS::EC2::NetworkAcl',
    'AWS::EC2::NetworkInterface',
    'AWS::EC2::LaunchTemplate',

    # Storage
    'AWS::S3::Bucket',
    'AWS::EFS::FileSystem',
    'AWS::EFS::MountTarget',
    'AWS::FSx::FileSystem',
    'AWS::S3::BucketPolicy',

    # Databases & Caches
    'AWS::RDS::DBInstance',
    'AWS::RDS::DBSubnetGroup',
    'AWS::DynamoDB::Table',
    'AWS::ElastiCache::CacheCluster',
    'AWS::Neptune::DBCluster',
    'AWS::DocumentDB::DBInstance',
    'AWS::DocumentDB::DBCluster',

    # IAM & Security
    'AWS::IAM::Role',
    'AWS::IAM::User',
    'AWS::IAM::Policy',
    'AWS::KMS::Key',
    'AWS::SecretsManager::Secret',
    'AWS::SSM::Parameter',

    # Serverless
    'AWS::Lambda::Function',
    'AWS::Lambda::Permission',
    'AWS::StepFunctions::StateMachine',
    'AWS::EventBridge::Rule',
    'AWS::AppSync::GraphQLApi',

    # Load Balancing & Networking
    'AWS::ElasticLoadBalancing::LoadBalancer',
    'AWS::ElasticLoadBalancingV2::LoadBalancer',
    'AWS::ElasticLoadBalancingV2::Listener',
    'AWS::ElasticLoadBalancingV2::TargetGroup',
    'AWS::CloudFront::Distribution',
    'AWS::Route53::HostedZone',
    'AWS::Route53::RecordSet',
    'AWS::GlobalAccelerator::Accelerator',
    'AWS::GlobalAccelerator::EndpointGroup',

    # Messaging & Queueing
    'AWS::SNS::Topic',
    'AWS::SQS::Queue',
    'AWS::MQ::Broker',

    # Monitoring & Logging
    'AWS::CloudWatch::Alarm',
    'AWS::CloudWatch::Dashboard',
    'AWS::CloudTrail::Trail',
    'AWS::XRay::SamplingRule',
    'AWS::XRay::Group',

    # API & Application Integration
    'AWS::ApiGateway::RestApi',
    'AWS::ApiGateway::Stage',
    'AWS::ApiGateway::Deployment',
    'AWS::AppMesh::Mesh',
    'AWS::AppMesh::VirtualNode',
    'AWS::AppMesh::VirtualService',
    'AWS::AppMesh::VirtualRouter',

    # Containers & Orchestration
    'AWS::ECS::Cluster',
    'AWS::ECS::Service',
    'AWS::ECS::TaskDefinition',
    'AWS::EKS::Cluster',
    'AWS::EKS::Nodegroup',
    'AWS::ECR::Repository',
    'AWS::Batch::JobQueue',
    'AWS::Batch::ComputeEnvironment',

    # Machine Learning / AI Services
    'AWS::SageMaker::NotebookInstance',
    'AWS::SageMaker::TrainingJob',
    'AWS::SageMaker::Model',
    'AWS::SageMaker::EndpointConfig',
    'AWS::SageMaker::Endpoint',
    'AWS::Comprehend::DocumentClassifier',
    'AWS::Comprehend::EntityRecognizer',
    'AWS::Rekognition::Project',
    'AWS::Rekognition::StreamProcessor',
    'AWS::Lex::Bot',
    'AWS::Polly::Lexicon',
    'AWS::Transcribe::MedicalVocabulary',
    'AWS::Forecast::Dataset',
    'AWS::Forecast::Predictor',
    'AWS::Forecast::Forecast',
    'AWS::Personalize::DatasetGroup',
    'AWS::Personalize::Campaign',
    
    # DevOps & CI/CD
    'AWS::CodeCommit::Repository',
    'AWS::CodeBuild::Project',
    'AWS::CodePipeline::Pipeline',
    'AWS::CodeDeploy::Application',
    'AWS::CodeDeploy::DeploymentGroup',
    'AWS::CloudFormation::Stack',
    'AWS::CloudFormation::StackSet',
    'AWS::CloudFormation::WaitCondition',

    # Networking / VPN
    'AWS::VPN::Connection',
    'AWS::VPN::Gateway',
    'AWS::DirectConnect::Connection',

    # IoT
    'AWS::IoT::Thing',
    'AWS::IoT::Policy',

    # Others
    'AWS::ElasticBeanstalk::Application',
    'AWS::ElasticBeanstalk::Environment',
    'AWS::StepFunctions::StateMachine',
    'AWS::Cloud9::EnvironmentEC2',

]


def get_all_resources(region, access_key, secret_key):
    config_client = boto3.client(
        'config',
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    all_resources = {}

    for rtype in resource_types:
        st.info(f"Discovering resources of type: {rtype}")
        try:
            paginator = config_client.get_paginator('list_discovered_resources')
            resources = []
            for page in paginator.paginate(resourceType=rtype):
                for resource in page['resourceIdentifiers']:
                    # Fetch latest config for each resource
                    try:
                        history = config_client.get_resource_config_history(
                            resourceType=rtype,
                            resourceId=resource['resourceId'],
                            limit=1
                        )
                        if history['configurationItems']:
                            resources.append(history['configurationItems'][0])
                    except ClientError as e:
                        st.warning(f"Error fetching config for {resource['resourceId']}: {e}")
            all_resources[rtype] = resources
        except ClientError as e:
            st.error(f"Error listing resources for {rtype}: {e}")
            all_resources[rtype] = []

    return all_resources

if st.button("Scan AWS Architecture"):
    if not access_key or not secret_key or not region:
        st.error("Please enter all AWS credentials and region.")
    else:
        with st.spinner("Scanning AWS Config... This may take a few moments."):
            try:
                resources = get_all_resources(region, access_key, secret_key)
                st.success("Scan complete!")

                # Display JSON in the app
                st.subheader("Discovered AWS Architecture JSON")
                st.json(resources)

                # Prepare downloadable JSON file
                json_data = json.dumps(resources, indent=4)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name="aws_config_inventory.json",
                    mime="application/json"
                )
            except ClientError as e:
                st.error(f"AWS Client error: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
