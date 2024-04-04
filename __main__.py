"""A Python Pulumi program"""

import pulumi
import os
import pulumi_docker as docker

config = pulumi.Config()
frontend_port = config.require_int("frontendPort")
backend_port = config.require_int("backendPort")
mongo_port = config.require_int("mongoPort")
mongo_host = config.require("mongoHost")
database = config.require("database")
node_environment = config.require("nodeEnvironment")
protocol = config.require("protocol")

stack = pulumi.get_stack()

backend_image_name = "backend"
backend = docker.RemoteImage(
    f"{backend_image_name}_image",
    name="pulumi/tutorial-pulumi-fundamentals-backend:latest",
)

frontend_image_name = "frontend"
frontend = docker.RemoteImage(
    f"{frontend_image_name}_image",
    name="pulumi/tutorial-pulumi-fundamentals-frontend:latest",
)

mongo = docker.RemoteImage(
    "mongo_image", name="pulumi/tutorial-pulumi-fundamentals-database-local:latest"
)

network = docker.Network("network", name=f"services_{stack}")

# Create the MongoDB container
mongo_container = docker.Container(
    "mongo_container",
    image=mongo.repo_digest,
    name=f"mongo-{stack}",
    ports=[docker.ContainerPortArgs(internal=mongo_port, external=mongo_port)],
    networks_advanced=[
        docker.ContainerNetworksAdvancedArgs(name=network.name, aliases=["mongo"])
    ],
)

backend_container = docker.Container(
    "backend_container",
    name=f"backend-{stack}",
    image=backend.repo_digest,
    ports=[docker.ContainerPortArgs(internal=backend_port, external=backend_port)],
    envs=[
        f"DATABASE_HOST={mongo_host}",
        f"DATABASE_NAME={database}",
        f"NODE_ENV={node_environment}",
    ],
    networks_advanced=[docker.ContainerNetworksAdvancedArgs(name=network.name)],
    opts=pulumi.ResourceOptions(depends_on=[mongo_container]),
)

# Create the frontend container
frontend_container = docker.Container(
    "frontend_container",
    image=frontend.repo_digest,
    name=f"frontend-{stack}",
    ports=[docker.ContainerPortArgs(internal=frontend_port, external=frontend_port)],
    envs=[
        f"PORT={frontend_port}",
        f"HTTP_PROXY=backend-{stack}:{backend_port}",
        f"PROXY_PROTOCOL={protocol}",
    ],
    networks_advanced=[docker.ContainerNetworksAdvancedArgs(name=network.name)],
)

pulumi.export("url", pulumi.Output.format("http://localhost:{0}", frontend_port))
