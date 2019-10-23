## AWSでサーバレスな動画解析(Rekognition)
こんにちは。
日々の業務ではインフラエンジニアをやっています。@hayaosatoです。

皆様は最近は動画解析などの技術も流行っていてそれらのSaaSも提供されていますね。
AWSでは[Amazon Rekognition](https://aws.amazon.com/jp/rekognition/)(Rekognition)というサービスが提供されています。
本記事ではこのRekognitionを使うためのサーバレスアーキテクチャを構築してみたいと思います。

### 構成
構成図は以下の通りです。

Rekognitionで動画解析を行うと、動画の長さによりますが解析時間がかかってしまいます。
Rekognitionでは解析時間の完了をAmazon SNS(以下、SNS)のトピックを発行することで通知してくれます。
今回はS3に動画がアップロードされたことをトリガにAWS Lambda(以下、Lambda)からRekognitonの動画解析開始
Rekognitionの動画解析完了後SNSトピックからLambdaを呼び出し、LambdaからRekognitonの解析結果を取得する
というアーキテクチャを作ってみます。

### S3 -> Lambda
Lambdaファンクションを作成し、トリガを設定します。
この際に注意すべきは動画はファイルサイズが大きくなりがちなので、
マルチパートアップロードの完了時もちゃんとトリガが飛ぶようにしておきましょう。

### Lambda -> Rekognition -> SNS
Rekognitionで解析を開始するためのLambdaファンクションを作成します。
言語はPythonにしました。ドキュメントは[こちら](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rekognition.html)。
今回は顔認識を使ってみることにしたので、`start_face_detection`を使用します。
```
response = client.start_face_detection(
    Video={
        'S3Object': {
            'Bucket': 'your-bucket-name',
            'Name': 'your-video-name'
        }
    },
    ClientRequestToken='string',
    NotificationChannel={
        'SNSTopicArn': 'your-sns-topic-arn',
        'RoleArn': 'your-role-arn-for-rekognition'
    }
)
```

ここで、`NotificationChannel`にSNSとROLEのARNを指定しています。
`SNSTopicArn`はその通りRekognitionが解析完了した際に通知を飛ばすためのSNSトピックのARNです。
`RoleArn`はRekognitionがSNSトピックを飛ばすためのRoleを与える必要があります。


### SNS -> Lambda -> Rekognition
Rekognitionから発行されたSNSトピックからLambdaが呼び出されるようにサブスクリプションを作成したら、
最後にLambdaからRekognitionに対して動画解析の結果を取得します。

Lambdaに届くeventの'Sns'キーのValueは以下のようになっています。
```=event['Records'][0]['Sns']
{
    'Type': 'Notification',
    'MessageId': 'xxxxxxxx',
    'TopicArn': 'arn:aws:sns:your-region:your-account-id:your-topic-arn',
    'Subject': None,
    'Message': '{"JobId":"xxxxxxxxxx","Status":"SUCCEEDED","API":"APINAME","Timestamp":1571799891913,"Video":{"S3ObjectName":"your-video.mp4","S3Bucket":"your-video-bucket"}}',
    'Timestamp': '2019-10-23T03:04:52.660Z',
    'SignatureVersion': '1',
    'Signature': 'xxxxxxxxx'
    'SigningCertUrl': 'https://sns.ap-northeast-1.amazonaws.com/SimpleNotificationService-xxxx.pem',
    'UnsubscribeUrl': 'https://sns.ap-northeast-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:xxxxxx',
    'MessageAttributes': {}
}
```
このようにして、Messageを取り出すことでRekognitionから結果を抜き出すための情報が揃います。
Messageから`JobId`を抜き出して、

(NextTokenは省略しています。)
```
response = client.get_face_detection(
    JobId='xxxxxx'
)
```
Rekognitionから解析結果のJSONを受け取りことができます。

### まとめ
このようにして、Rekognitionを利用してサーバレスなアーキテクチャを作成してみました。
サーバレスでイベントドリブンってやっぱりいいですね
