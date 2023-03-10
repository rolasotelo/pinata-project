import json
import base64
import openai
import os
import boto3
import uuid
import datetime

table_name = os.environ.get("TABLE", "Images")
region = os.environ.get("REGION", "eu-central-1")
aws_environment = os.environ.get("AWSENV", "Local")
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "")
# delete first and last character of the string
trimmed_origin = allowed_origins[1:-1]

if aws_environment == "Local":
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
        return {"statusCode": 400, "headers": {"Access-Control-Allow-Origin": trimmed_origin},
                "body": "Bad request"}

    prompt = event["queryStringParameters"]["prompt"]
    stage = event["queryStringParameters"]["stage"]
    stage = stage or "no-stage"
    image_url = ""
    input_url = ""
    prompt_context = ""
    if "image_url" in event["queryStringParameters"]:
        image_url = event["queryStringParameters"]["image_url"]
    if "input_url" in event["queryStringParameters"]:
        input_url = event["queryStringParameters"]["input_url"]
    if "prompt_context" in event["queryStringParameters"]:
        prompt_context_64 = event["queryStringParameters"]["prompt_context"]
        context_base64_bytes = prompt_context_64.encode('ascii')
        context_message_bytes = base64.b64decode(context_base64_bytes)
        prompt_context = context_message_bytes.decode('ascii')

    if image_url != "":
        try:
            base64_bytes = prompt.encode('ascii')
            message_bytes = base64.b64decode(base64_bytes)
            message = message_bytes.decode('ascii')
            time_epoch = datetime.datetime.now().timestamp()
            expiration_time_epoch = time_epoch + 3600

            item = {
                "id": {"S": str(uuid.uuid4())},
                "created_dt": {"S": str(time_epoch)},
                "prompt": {"S": message},
                "stage": {"S": str(stage)},
                "image_url": {"S": image_url},
                "input_url": {"S": input_url},
                "prompt_context": {"S": prompt_context},
                "expiration_dt": {"S": str(expiration_time_epoch)}
            }
            ddb_client.put_item(TableName=table_name, Item=item)
            return {"statusCode": 201, "headers": {"Access-Control-Allow-Origin": trimmed_origin},
                    "body": json.dumps(
                        {"image_url": image_url, "input_url": input_url, "prompt": message,
                         "prompt_context": prompt_context, "id": item["id"]["S"]})}
        except Exception as e:
            return {"statusCode": 500, "headers": {"Access-Control-Allow-Origin": trimmed_origin},
                    "body": json.dumps({"error": str(e)})}

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
        time_epoch = datetime.datetime.now().timestamp()
        expiration_time_epoch = time_epoch + 3600

        item = {
            "id": {"S": str(uuid.uuid4())},
            "created_dt": {"S": str(time_epoch)},
            "prompt": {"S": message},
            "stage": {"S": str(stage)},
            "image_url": {"S": image_url},
            "input_url": {"S": ""},
            "prompt_context": {"S": prompt_context},
            "expiration_dt": {"S": str(expiration_time_epoch)}
        }
        ddb_client.put_item(TableName=table_name, Item=item)
        return {"statusCode": 201, "headers": {"Access-Control-Allow-Origin": trimmed_origin},
                "body": json.dumps(
                    {"image_url": image_url, "input_url": "", "prompt": message, "prompt_context": prompt_context,
                     "id": item["id"]["S"]})}
    except Exception as e:
        return {"statusCode": 500, "headers": {"Access-Control-Allow-Origin": trimmed_origin},
                "body": json.dumps({"error": str(e)})}
