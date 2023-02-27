import os
import boto3
import json
import datetime

table_name = os.environ.get("TABLE")
region = os.environ.get("REGION")
aws_environment = os.environ.get("AWSENV", "AWS")
index_name = os.environ.get("INDEX_NAME")


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
    limit_creation = datetime.datetime.now()-datetime.timedelta(hours=1)
    limit_creation_epoch = str(limit_creation.timestamp())

    try:
        # get item from dynamodb with global secondary index
        ddb_response = ddb_client.query(
            TableName=table_name,
            Select="SPECIFIC_ATTRIBUTES",
            IndexName=index_name,
            Limit=10,
            ScanIndexForward=False,
            KeyConditionExpression="stage = :stage AND created_dt > :limit_creation",
            ProjectionExpression="image_url, prompt, expiration_dt",
            ExpressionAttributeValues={
                ":stage": {"N": stage},
                ":limit_creation": {"S": limit_creation_epoch}
            }
        )

        images = []
        for item in ddb_response["Items"]:
            add_item = dict(image_url=item["image_url"]['S'], prompt=item["prompt"]['S'],
                            expiration_dt=item["expiration_dt"]['S'])
            images.append(add_item)

        return {"statusCode": 201, "headers": {}, "body": json.dumps({"images": images})}
    except Exception as e:
        print(e)
        return {"statusCode": 500, "headers": {}, "body": "Internal Server Error"}