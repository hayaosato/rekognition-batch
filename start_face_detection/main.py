"""
s3 upload -> rekognition face-detection -> sns

環境変数
    - SLACK_API_KEY: slack通知のためのAPIキー
    - SNS_TOPIC_ARN: rekognition解析後の通知先SNSのARN
    - ROLE_ARN: rekognitionからSNSに通知を飛ばすためのrole
"""
import os
import boto3
from slacker import Slacker  # pylint: disable=import-error


def send_slack(message, channel='#general'):
    """
    slack nortification
    """
    slack_api_key = os.environ['SLACK_API_KEY']
    if slack_api_key != "":
        slack = Slacker(slack_api_key)
        slack.chat.post_message(channel, message)


def rekognition(bucket, video_path):
    """
    call rekognition
    """
    client = boto3.client('rekognition', region_name='ap-northeast-1')
    response = client.start_face_detection(
        Video={
            'S3Object': {
                'Bucket': bucket,
                'Name': video_path
            }
        },
        NotificationChannel={
            'SNSTopicArn': os.environ['SNS_TOPIC_ARN'],
            'RoleArn': os.environ['ROLE_ARN']
        }
    )
    message = '顔認識解析開始\n動画: s3://{0}/{1}\njobID: {2}'.format(
        bucket, video_path, response['JobId']
    )
    send_slack(message)
    return response['JobId']


def main(event, _):
    """
    eventから動画のあるバケットとファイル名を取得して、rekognitionに投げる
    """
    rekognition(
        event['Records'][0]['s3']['bucket']['name'],
        event['Records'][0]['s3']['object']['key']
    )
