import boto3
import json
import urllib.request
import urllib.error

def lambda_handler(event, context):
    try:
        # Check if 'Records' exist in the event
        if 'Records' not in event or len(event['Records']) == 0:
            raise ValueError("Event does not contain S3 records")

        s3_info = event['Records'][0]['s3']
        s3_bucket = s3_info['bucket']['name']
        s3_key = s3_info['object']['key']
        
        print(f"Received event: {json.dumps(event)}")
        print(f"Processing image: s3://{s3_bucket}/{s3_key}")

        # Rekognition label detection
        rekog = boto3.client('rekognition')
        response = rekog.detect_labels(
            Image={'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}},
            MaxLabels=50,
            MinConfidence=70
        )

        detected_labels = [label['Name'] for label in response['Labels']]
        print(f"Detected labels: {detected_labels}")

        if not detected_labels:
            scene = "unknown scene"
        elif len(detected_labels) == 1:
            scene = f"{detected_labels[0]}"
        elif len(detected_labels) == 2:
            scene = f"{detected_labels[0]} and {detected_labels[1]}"
        else:
            scene = f"{', '.join(detected_labels[:-1])}, and {detected_labels[-1]}"

        # Generate the prompt
        prompt = (
            f"A short news article must be written based only on the given list of labels: {scene}. "
            f"With these elements, determine a theme (e.g. sports, technology, politics, etc.), and based on that, generate a fictional news article. "
            f"Start with a staccato lead. "
            f"The article must be written using only the physical objects or visible elements that are named in the label list. "
            f"No object, character, or visible detail that is not listed should be included. "
            f"If a label refers to something abstract, such as an emotion or activity, keep it abstract. "
            f"Do not turn it into a person, an action, or an event. "
            f"Do not create agents, events, sounds, or extra visual details. "
            f"Use plain English, philosophical, political, unslanted, eloquent, and abstract language, indirect phrasing, and also a natural and conversational tone with a sense of humor. "
            f"Varied and metaphorical expressions should be used based on the labels, when possible, and label words should not be repeated exactly. "
            f"The article should be clear, faithful to the labels, and written in full sentences, 250 to 300 words. "
            f"Keep your descriptions grounded, witty, mature, purposeful, full of sense, sound, logical and valid, and giving precious and brilliant life lessons. Do not add anything extra."
        )

        print(f"Prompt: {prompt}")

        # OpenAI API call
        api_url = "https://is215-openai.upou.io/v1/chat/completions"
        api_key = "galang-0yvua8ytST"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "you are a journalist that writes only based on the facts given to you and nothing more."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        req = urllib.request.Request(api_url, method='POST', headers=headers, data=json.dumps(payload).encode())
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            story = data["choices"][0]["message"]["content"].strip()

        print(f"Generated story: {story}")

        # Save to S3
        s3_client = boto3.client('s3')
        output_key = f"articles/{s3_key.rsplit('.', 1)[0]}.txt"
        s3_client.put_object(Bucket=s3_bucket, Key=output_key, Body=story.encode(), ContentType='text/plain')
        print(f"Article saved to: s3://{s3_bucket}/{output_key}")

        # Return correct key (`message`) and added article filename
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "bucket": s3_bucket,
                "key": s3_key,
                "labels": detected_labels,
                "prompt": prompt,
                "message": story,  # FIXED
                "article_key": output_key,
                "article_s3_url": f"https://{s3_bucket}.s3.amazonaws.com/{output_key}"  # optional public URL
            })
        }

    except urllib.error.URLError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"API request failed: {str(e)}"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Unhandled error: {str(e)}"})
        }
