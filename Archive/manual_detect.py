import boto3

def lambda_handler(event, context):
    s3_bucket = 'is215-final-haongos'
    s3_key = 'dogcat.jpg'  # Replace with your actual image key

    client = boto3.client('rekognition')

    response = client.detect_labels(
        Image={'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}},
        MaxLabels=50,
        MinConfidence=70
    )

    # Check for specific objects
    detected_labels = [label['Name'] for label in response['Labels']]
    found_objects = []

    for obj in ['Person', 'Car', 'Vehicle', 'Bus', 'Truck']:
        if obj in detected_labels:
            found_objects.append(obj)

    return {
        'statusCode': 200,
        'body': {
            'foundObjects': found_objects,
            'allLabels': detected_labels
        }
    }
