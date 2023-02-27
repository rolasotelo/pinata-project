run_dev: is_dynamodb_local_running validate_template build
	@echo "Running in development mode 🔥"
	@sam local start-api \
     --docker-network lambda-local \
     --parameter-overrides 'AWSENV=AWS_SAM_LOCAL'

deploy: validate_template build
	@echo "Deploying 🚀"
	@sam deploy --guided

build:
	@echo "Building 🏗"
	@sam build

validate_template:
	@echo "Validating template 🚓"
	@aws cloudformation validate-template --template-body file://template.yaml

# docker container for dynamodb local is running
is_dynamodb_local_running:
	@echo "Checking if DynamoDB Local is running 🎬"
	@docker inspect -f '{{.State.Running}}' dynamodb

run_dynamodb_local:
	@echo "Running DynamoDB Local 🐳"
	@docker run \
	 -p 8000:8000 \
	 -d \
	 --rm \
	 --network lambda-local \
	 --name dynamodb \
	 -v /Users/rolandosotelo/.docker/dynamodb:/data/ \
	 amazon/dynamodb-local \
	 -jar DynamoDBLocal.jar -sharedDb -dbPath /data