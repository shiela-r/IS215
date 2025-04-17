import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def story_generator(labels):
    # Sentence builder
    if not labels:
        scene = "unknown scene"
    elif len(labels) == 1:
        scene = f"scene with: {labels[0]}"
    elif len(labels) == 2:
        scene = f"scene with:{labels[0]} and {labels[1]}"
    else:
        scene = f"scene with:{', '.join(labels[:-1])}, and {labels[-1]}"

    # Creating prompt
    prompt = (f"Write a fictional article based on this scene: {scene}.")
    
    # Calling Open API
    api_url = "https://is215-openai.upou.io/v1/chat/completions"
    api_key = os.environ.get("OPENAI_API_KEY")

    headers = {"Content-type": "application/json", "Authorization": f"Bearer {api_key}" }
    payload = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        story = data["choices"][0]["message"]["content"].strip()
        return prompt, story
    except ValueError:
        story = f"Error: cannot decode response as JSON.\nRaw response:\n{response.text}"
        return prompt, story
    except Exception as e:
        return prompt, f"Error: {str(e)}"
    
    # Note: Below is include for testing only
if __name__ == "__main__":
    #Rekog input
    test_labels = ["Studying", "Happiness", "Books", "Library", "Quiet"]

    prompt_text, story_output = story_generator(test_labels)
    print("\n--- Prompt Sent to GPT - 3.5 ---")
    print(prompt_text)
    print("\n OpenAI-generated story ---")
    print(story_output)
