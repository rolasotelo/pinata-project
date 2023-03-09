import os
import boto3
import json

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

    image_id = event["queryStringParameters"]["id"]

    try:
        key = {
            "id": image_id,
        }
        ddb_client.delete_item(TableName=table_name, Key=key)
        return {"statusCode": 201, "headers": {"Access-Control-Allow-Origin": trimmed_origin},
                "body": json.dumps({"id": id})}
    except Exception as e:
        return {"statusCode": 500, "headers": {"Access-Control-Allow-Origin": trimmed_origin},
                "body": json.dumps({"error": str(e)})}
