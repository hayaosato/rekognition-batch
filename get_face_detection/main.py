"""
sns -> lambda -> rekognition

環境変数
    - SLACK_API_KEY: slack通知のためのAPIキー
"""
import os
import json
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


def get_face_detection(job_id, next_token=''):
    """
    rekognitionから解析結果を取得
    """
    client = boto3.client('rekognition', region_name='ap-northeast-1')
    response = client.get_face_detection(
        JobId=job_id,
        NextToken=next_token
    )
    return response


def main(event, _):
    """
    eventからJOBIDを抜き出してRekognitionに投げる
    """
    json_contents = json.loads(event['Records'][0]['Sns']['Message'])
    result_json = get_face_detection(json_contents["JobId"])
    send_slack(result_json)
