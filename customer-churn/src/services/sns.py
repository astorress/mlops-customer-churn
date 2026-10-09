import boto3

CLIENT = boto3.client("sns")


def publish(topic_arn: str, subject: str, message: str) -> None:
    # SNS subjects: max 100 chars.
    CLIENT.publish(TopicArn=topic_arn, Subject=subject[:100], Message=message)
