import boto3
import json
import urllib.request 
import urllib.error
import ast  

def lambda_handler(event, context):
    try:
        if 'Records' not in event or len(event['Records']) == 0:
            raise ValueError("Event does not contain S3 records")

        s3_info = event['Records'][0]['s3']
        s3_bucket = s3_info['bucket']['name']
        s3_key = s3_info['object']['key']

        print(f"Received event: {json.dumps(event)}")
        print(f"Processing image: s3://{s3_bucket}/{s3_key}")

        if not s3_key.lower().endswith(('.jpg', '.jpeg', '.png')):
            raise ValueError(f"Unsupported file type: {s3_key}")

        client = boto3.client('rekognition')
        response = client.detect_labels(
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

        prompt = (
            f"Given the labels: {scene}, generate a JSON object with two fields: "
            f"'title' (a short, compelling headline using only the label concepts, basing from the theme and most important concepts of the body, max 12 words) and "
            f"'body' (a 250–300 word article strictly based on the same labels). "
            f"The body must:"
            f"a) With these elements (labels), determine a theme (e.g. sports, technology, politics, etc.), and based on that, generate a fictional news article. "
            f"b) Start with a staccato lead. "
            f"c) The article must be written using only the physical objects or visible elements that are named in the label list. "
            f"d) No object, character, or visible detail that is not listed should be included. "
            f"e) If a label refers to something abstract, such as an emotion or activity, keep it abstract. "
            f"f) Do not turn it into a person, an action, or an event. "
            f"g) Do not create agents, events, sounds, or extra visual details. "
            f"h) Use plain English, philosophical, political, unslanted, eloquent, and abstract language, indirect phrasing, and also a natural and conversational tone with a sense of humor. "
            f"i) Varied and metaphorical expressions should be used based on the labels, when possible, and label words should not be repeated exactly. "
            f"j) The article should be clear, faithful to the labels, and written in full sentences."
            f"k) Keep your descriptions grounded, witty, mature, purposeful, full of sense, sound, logical and valid, and giving precious and brilliant life lessons. Do not add anything extra."
            f"Output only a JSON object: {{'title': '...', 'body': '...'}}."
        )

        print(f"Prompt: {prompt}")

        api_url = "https://is215-openai.upou.io/v1/chat/completions"
        api_key = os.environ.get("OPENAI_API_KEY")

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

        try:
            req = urllib.request.Request(api_url, method='POST', headers=headers, data=json.dumps(payload).encode())
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read())
                response_text = data["choices"][0]["message"]["content"].strip()
                print(f"Raw OpenAI response: {response_text}")
                parsed = ast.literal_eval(response_text)
                title = parsed.get("title", "Untitled")
                body = parsed.get("body", "")

        except Exception as e:
            print(f"Error during OpenAI API request: {str(e)}")  
            raise

        full_article = f"{title}\n\n{body}"
        filename = s3_key.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        output_key = f"articles/{filename}.txt"

        s3_client = boto3.client('s3')

        
        print(f"Writing to S3: Bucket={s3_bucket}, Key={output_key}")  
        print(f"Content to write: {full_article}")  

        try:
            print(f"Writing to S3: Bucket={s3_bucket}, Key={output_key}")
            print(f"Content to write: {full_article}")

            s3_client.put_object(
                Bucket=s3_bucket,
                Key=output_key,
                Body=full_article.encode(),
                ContentType='text/plain',
                
            )
            print(f"File successfully written to s3://{s3_bucket}/{output_key}")  

        except Exception as e:
            print(f"Error writing to S3: {str(e)}")  
            raise

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
                "title": title,
                "body": body,
                "article_s3_url": f"https://{s3_bucket}.s3.amazonaws.com/{output_key}"
            })
        }

    except urllib.error.URLError as e:
        print(f"URL Error: {str(e)}")  
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"API request failed: {str(e)}"})
        }

    except Exception as e:
        print(f"Unhandled error: {str(e)}")  
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Unhandled error: {str(e)}"})
        }
