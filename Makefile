start_dev: run_dynamodb_local_if_not_running build
	@echo "Starting development mode ๐ก"
	@sam local start-api \
     --docker-network lambda-local \
     --parameter-overrides "ParameterKey=awsEnv,ParameterValue=Local"

stop_dev: stop_dynamodb_local
	@echo "Stopping development mode ๐"

deploy: validate_template build
	@echo "Deploying ๐"
	@sam deploy --guided

build:
	@echo "Building ๐"
	@sam build

validate_template:
	@echo "Validating template ๐"
	@aws cloudformation validate-template --template-body file://template.yaml

run_dynamodb_local:
	@echo "Running DynamoDB Local ๐ณ"
	@docker run \
	 -p 8000:8000 \
	 -d \
	 --rm \
	 --network lambda-local \
	 --name dynamodb \
	 -v /Users/rolandosotelo/.docker/dynamodb:/data/ \
	 amazon/dynamodb-local \
	 -jar DynamoDBLocal.jar -sharedDb -dbPath /data

stop_dynamodb_local:
	@echo "Stopping DynamoDB Local ๐งน"
	@docker stop dynamodb

# run dynamodb local if not running
run_dynamodb_local_if_not_running:
	@echo "Checking if DynamoDB Local is running ๐ฌ"
	@docker container inspect dynamodb > /dev/null 2>&1 || make run_dynamodb_local

delete_local_dynamodb_table:
	@echo "Deleting local DynamoDB table ๐ฅ"
	@aws dynamodb delete-table --table-name Images --endpoint-url http://localhost:8000