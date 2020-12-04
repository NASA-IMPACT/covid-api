"""Construct App."""

import os
import shutil
from typing import Any, Union

import config
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_elasticache as escache
from aws_cdk import aws_events, aws_events_targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda, core

iam_policy_statement = iam.PolicyStatement(
    actions=["s3:*"], resources=[f"arn:aws:s3:::{config.BUCKET}*"]
)

DEFAULT_ENV = dict(
    CPL_TMPDIR="/tmp",
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
    GDAL_CACHEMAX="75%",
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
    GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
    GDAL_HTTP_MULTIPLEX="YES",
    GDAL_HTTP_VERSION="2",
    PYTHONWARNINGS="ignore",
    VSI_CACHE="TRUE",
    VSI_CACHE_SIZE="1000000",
)


class covidApiLambdaStack(core.Stack):
    """
    Covid API Lambda Stack

    This code is freely adapted from
    - https://github.com/leothomas/titiler/blob/10df64fbbdd342a0762444eceebaac18d8867365/stack/app.py author: @leothomas
    - https://github.com/ciaranevans/titiler/blob/3a4e04cec2bd9b90e6f80decc49dc3229b6ef569/stack/app.py author: @ciaranevans

    """

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        memory: int = 1024,
        timeout: int = 30,
        concurrent: int = 100,
        env: dict = {},
        code_dir: str = "./",
        **kwargs: Any,
    ) -> None:
        """Define stack."""
        super().__init__(scope, id, *kwargs)

        # add cache
        vpc = ec2.Vpc(self, f"{id}-vpc")
        sb_group = escache.CfnSubnetGroup(
            self,
            f"{id}-subnet-group",
            description=f"{id} subnet group",
            subnet_ids=[sb.subnet_id for sb in vpc.private_subnets],
        )

        sg = ec2.SecurityGroup(self, f"{id}-cache-sg", vpc=vpc)
        cache = escache.CfnCacheCluster(
            self,
            f"{id}-cache",
            cache_node_type=config.CACHE_NODE_TYPE,
            engine=config.CACHE_ENGINE,
            num_cache_nodes=config.CACHE_NODE_NUM,
            vpc_security_group_ids=[sg.security_group_id],
            cache_subnet_group_name=sb_group.ref,
        )

        vpc_access_policy_statement = iam.PolicyStatement(
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "ec2:CreateNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DeleteNetworkInterface",
            ],
            resources=["*"],
        )

        lambda_env = DEFAULT_ENV.copy()
        lambda_env.update(
            dict(
                MODULE_NAME="covid_api.main",
                VARIABLE_NAME="app",
                WORKERS_PER_CORE="1",
                LOG_LEVEL="error",
                MEMCACHE_HOST=cache.attr_configuration_endpoint_address,
                MEMCACHE_PORT=cache.attr_configuration_endpoint_port,
                DATASET_METADATA_FILENAME=env["DATASET_METADATA_FILENAME"],
                DATASET_METADATA_GENERATOR_FUNCTION_NAME=env[
                    "DATASET_METADATA_GENERATOR_FUNCTION_NAME"
                ],
            )
        )

        lambda_function = aws_lambda.Function(
            self,
            f"{id}-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_7,
            code=self.create_package(code_dir),
            handler="handler.handler",
            memory_size=memory,
            reserved_concurrent_executions=concurrent,
            timeout=core.Duration.seconds(timeout),
            environment=lambda_env,
            vpc=vpc,
        )
        lambda_function.add_to_role_policy(iam_policy_statement)
        lambda_function.add_to_role_policy(vpc_access_policy_statement)

        # defines an API Gateway Http API resource backed by our "dynamoLambda" function.
        apigw.HttpApi(
            self,
            f"{id}-endpoint",
            default_integration=apigw.LambdaProxyIntegration(handler=lambda_function),
        )

    def create_package(self, code_dir: str) -> aws_lambda.Code:
        """Build docker image and create package."""
        # print('building lambda package via docker')
        # print(f'code dir: {code_dir}')
        # client = docker.from_env()
        # print('docker client up')
        # client.images.build(
        #     path=code_dir,
        #     dockerfile="Dockerfiles/lambda/Dockerfile",
        #     tag="lambda:latest",
        # )
        # print('docker image built')
        # client.containers.run(
        #     image="lambda:latest",
        #     command="/bin/sh -c 'cp /tmp/package.zip /local/package.zip'",
        #     remove=True,
        #     volumes={os.path.abspath(code_dir): {"bind": "/local/", "mode": "rw"}},
        #     user=0,
        # )

        return aws_lambda.Code.asset(os.path.join(code_dir, "package.zip"))

        # Code.asset is deprecated - see: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_lambda/Code.html

        # return aws_lambda.Code.from_asset(
        #     path=os.path.join(code_dir, "package.zip"),
        #     bundling=core.BundlingOptions(
        #         image=core.BundlingDockerImage.from_asset(
        #             path=os.path.join(code_dir, "Dockerfiles/lambda/"),
        #             # file="Dockerfile",
        #         ),
        #         command="/bin/sh -c 'cp /tmp/package.zip /local/package.zip'",
        #         volumes=core.DockerVolume(
        #             container_path="/local/", host_path=os.path.abspath(code_dir)
        #         ),
        #         user="0",
        #     ),
        # )


class covidApiECSStack(core.Stack):
    """Covid API ECS Fargate Stack."""

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        cpu: Union[int, float] = 256,
        memory: Union[int, float] = 512,
        mincount: int = 1,
        maxcount: int = 50,
        env: dict = {},
        code_dir: str = "./",
        **kwargs: Any,
    ) -> None:
        """Define stack."""
        super().__init__(scope, id, *kwargs)

        vpc = ec2.Vpc(self, f"{id}-vpc", max_azs=2)

        cluster = ecs.Cluster(self, f"{id}-cluster", vpc=vpc)

        task_env = DEFAULT_ENV.copy()
        task_env.update(
            dict(
                MODULE_NAME="covid_api.main",
                VARIABLE_NAME="app",
                WORKERS_PER_CORE="1",
                LOG_LEVEL="error",
            )
        )
        task_env.update(env)

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            f"{id}-service",
            cluster=cluster,
            cpu=cpu,
            memory_limit_mib=memory,
            desired_count=mincount,
            public_load_balancer=True,
            listener_port=80,
            task_image_options=dict(
                image=ecs.ContainerImage.from_asset(
                    code_dir,
                    exclude=["cdk.out", ".git"],
                    file="Dockerfiles/ecs/Dockerfile",
                ),
                container_port=80,
                environment=task_env,
            ),
        )

        scalable_target = fargate_service.service.auto_scale_task_count(
            min_capacity=mincount, max_capacity=maxcount
        )

        # https://github.com/awslabs/aws-rails-provisioner/blob/263782a4250ca1820082bfb059b163a0f2130d02/lib/aws-rails-provisioner/scaling.rb#L343-L387
        scalable_target.scale_on_request_count(
            "RequestScaling",
            requests_per_target=50,
            scale_in_cooldown=core.Duration.seconds(240),
            scale_out_cooldown=core.Duration.seconds(30),
            target_group=fargate_service.target_group,
        )

        # scalable_target.scale_on_cpu_utilization(
        #     "CpuScaling", target_utilization_percent=70,
        # )

        fargate_service.service.connections.allow_from_any_ipv4(
            port_range=ec2.Port(
                protocol=ec2.Protocol.ALL,
                string_representation="All port 80",
                from_port=80,
            ),
            description="Allows traffic on port 80 from NLB",
        )


class covidApiDatasetMetadataGeneratorStack(core.Stack):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        dataset_metadata_filename: str,
        dataset_metadata_generator_function_name: str,
        code_dir: str = "./",
        **kwargs: Any,
    ) -> None:
        """Define stack."""
        super().__init__(scope, id, *kwargs)

        base = os.path.abspath(os.path.join("covid_api", "db", "static"))
        lambda_deployment_package_location = os.path.abspath(
            os.path.join(code_dir, "lambda", "dataset_metadata_generator", "src")
        )
        for e in ["datasets", "sites"]:
            self.copy_metadata_files_to_lambda_deployment_package(
                from_dir=os.path.join(base, e),
                to_dir=os.path.join(lambda_deployment_package_location, e),
            )

        dataset_metadata_updater_function = aws_lambda.Function(
            self,
            f"{id}-metadata-updater-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            code=aws_lambda.Code.from_asset(lambda_deployment_package_location),
            handler="main.handler",
            environment={"DATASET_METADATA_FILENAME": dataset_metadata_filename},
            function_name=dataset_metadata_generator_function_name,
        )

        for e in ["datasets", "sites"]:
            shutil.rmtree(os.path.join(lambda_deployment_package_location, e))

        aws_events.Rule(
            self,
            f"{id}-metadata-update-daily-trigger",
            # triggers everyday
            schedule=aws_events.Schedule.rate(duration=core.Duration.days(1)),
            targets=[
                aws_events_targets.LambdaFunction(dataset_metadata_updater_function)
            ],
        )

    def copy_metadata_files_to_lambda_deployment_package(self, from_dir, to_dir):
        files = [
            os.path.abspath(os.path.join(d, f))
            for d, _, fnames in os.walk(from_dir)
            for f in fnames
            if f.endswith(".json")
        ]

        try:
            os.mkdir(to_dir)
        except FileExistsError:
            pass

        for f in files:
            shutil.copy(f, to_dir)


app = core.App()


# Tag infrastructure
for key, value in {
    "Project": config.PROJECT_NAME,
    "Stack": config.STAGE,
    "Owner": os.environ.get("OWNER"),
    "Client": os.environ.get("CLIENT"),
}.items():
    if value:
        core.Tag.add(app, key, value)

ecs_stackname = f"{config.PROJECT_NAME}-ecs-{config.STAGE}"
covidApiECSStack(
    app,
    ecs_stackname,
    cpu=config.TASK_CPU,
    memory=config.TASK_MEMORY,
    mincount=config.MIN_ECS_INSTANCES,
    maxcount=config.MAX_ECS_INSTANCES,
    env=config.ENV,
)

# lambda_stackname = f"{config.PROJECT_NAME}-lambda-{config.STAGE}"
# covidApiLambdaStack(
#     app,
#     lambda_stackname,
#     memory=config.MEMORY,
#     timeout=config.TIMEOUT,
#     concurrent=config.MAX_CONCURRENT,
#     env=config.ENV,
# )

dataset_metadata_generator_stackname = (
    f"{config.PROJECT_NAME}-dataset-metadata-generator-{config.STAGE}"
)
covidApiDatasetMetadataGeneratorStack(
    app,
    dataset_metadata_generator_stackname,
    dataset_metadata_filename=config.DATASET_METADATA_FILENAME,
    dataset_metadata_generator_function_name=config.DATASET_METADATA_GENERATOR_FUNCTION_NAME,
)

app.synth()
