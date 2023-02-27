run_dev:
	@echo "Running in development mode 🔥"
	@sam local start-api \
     --docker-network lambda-local \
     --parameter-overrides 'AWSENV=AWS_SAM_LOCAL'

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