import json
import base64
import openai
import os
import boto3
import uuid
import datetime

table_name = os.environ.get("TABLE", "Images")
region = os.environ.get("REGION", "eu-central-1")
aws_environment = os.environ.get("AWSENV", "AWS")


if aws_environment == "AWS_SAM_LOCAL":
    ddb_client = boto3.client(
        "dynamodb", endpoint_url="http://dynamodb:8000"
    )
else:
    ddb_client = boto3.client(
        "dynamodb", region_name=region
    )

# Create a Secrets Manager client
session = boto3.session.Session()
sm_client = session.client(
    service_name='secretsmanager',
    region_name=region
)
secret_name = "openai-key"


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    if not event["queryStringParameters"] or event["queryStringParameters"] == "":
        return {"statusCode": 400, "headers": {}, "body": "Bad request"}

    prompt = event["queryStringParameters"]["prompt"]
    stage = event["queryStringParameters"]["stage"]
    stage = stage or "no-stage"

    try:

        get_secret_value_response = sm_client.get_secret_value(
            SecretId=secret_name
        )
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        openai.api_key = secret_dict["OPENAI_KEY"]

        base64_bytes = prompt.encode('ascii')
        message_bytes = base64.b64decode(base64_bytes)
        message = message_bytes.decode('ascii')
        openai_response = openai.Image.create(
            prompt=message,
            n=1,
            size="1024x1024"
        )
        image_url = openai_response['data'][0]['url']
        item = {
            "id": {"S": str(uuid.uuid4())},
            "created_dt": {"S": str(datetime.datetime.now())},
            "prompt": {"S": message},
            "stage": {"N": str(stage)},
            "image_url": {"S": image_url},
            "expiration_dt": {"S": str(datetime.datetime.now() + datetime.timedelta(hours=1))}
        }
        ddb_client.put_item(TableName=table_name, Item=item)
        return {"statusCode": 201, "headers": {}, "body": json.dumps({"url": image_url, "prompt": message})}
    except Exception as e:
        print(e)
        return {"statusCode": 500, "headers": {}, "body": "Internal Server Error"}
