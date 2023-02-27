import os
import boto3
import json

table_name = os.environ.get("TABLE", "Images")
region = os.environ.get("REGION", "eu-central-1")
aws_environment = os.environ.get("AWSENV", "AWS")
index_name = os.environ.get("INDEX_NAME", "stage-created_dt")


if aws_environment == "AWS_SAM_LOCAL":
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
        return {"statusCode": 400, "headers": {}, "body": "Bad request"}

    stage = event["queryStringParameters"]["stage"]
    stage = stage or "no-stage"
    print('index_name', index_name)

    try:
        # get item from dynamodb with global secondary index
        ddb_response = ddb_client.query(
            TableName=table_name,
            Select="SPECIFIC_ATTRIBUTES",
            IndexName="stage-created_dt",
            Limit=10,
            ScanIndexForward=False,
            KeyConditionExpression="stage = :stage",
            ProjectionExpression="image_url, prompt",
            ExpressionAttributeValues={
                ":stage": {"N": stage}
            }
        )
        return {"statusCode": 201, "headers": {}, "body": json.dumps({"images": ddb_response["Items"]})}
    except Exception as e:
        print(e)
        return {"statusCode": 500, "headers": {}, "body": "Internal Server Error"}