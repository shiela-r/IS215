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
        scene = f"{labels[0]}"
    elif len(labels) == 2:
        scene = f"{labels[0]} and {labels[1]}"
    else:
        scene = f"{', '.join(labels[:-1])}, and {labels[-1]}"

    # Creating prompt
    prompt = (f"A short news article must be written based only on the given list of labels: {scene}"
              f"With these elements, determine a theme (e.g. sports, technology,politics, etc and based from that, generate a fictional news article."
              f"Start with a staccato lead."
              f"The article must be written using only the physical objects or visible elements that are named in the label list."
              f"No object, character, or visible detail that is not listed should be included."
              f"If a label refers to something abstract, such as an emotion or activity, keep it abstract."
              f"Do not turn it into a person, an action, or an event."
              f"Treat nominalized words like “Studying” or “Happiness” as they are."
              f"Do not convert them into subject-verb-object form."
              f"Do not add people doing the action unless the label directly includes them."
              f"You may describe general uses or cultural associations related to the labels, but only if it is clear that they are not visible in the image."
              f"Do not create agents, events, sounds, or extra visual details."
              f"Do not imply that anything is seen in the image unless it is listed in the labels."
              f"Use plain English, philosophical, political, unslanted, eloquent, and abstract language, indirect phrasing, and also natural and conversational tone and with sense of humor."
              f"Varied and metaphorical expressions should be used based on the labels, when possible, and label words should not be repeated exactly."
              f"You may include vague or suggestive descriptions, as long as you stay within what the label list allows."
              f"The article should be clear, faithful to the labels, and written in full sentences, 250 to 300 words."
              f"Keep your descriptions grounded, witty, mature, purposeful, full of sense, sound, logical and valid, and giving precious and brilliant life lessons. Do not add anything extra."
              f"Put the determined theme right below the end of the article. Precede it with 'Theme: ")
    # the last line in the prompt can be removed once finalized, it is just for checking what them does the AI detect
    # based from the labels provided (e.g. detected by AWS Rekognition)
    
    # Calling Open API
    api_url = "https://is215-openai.upou.io/v1/chat/completions"
    api_key = os.environ.get("OPENAI_API_KEY")

    headers = {"Content-type": "application/json", "Authorization": f"Bearer {api_key}" }
    payload = {"model": "gpt-3.5-turbo",
               "messages": [
                            {"role": "system", "content": "you are a journalist that writes only based on the facts"
                                                          "given to you and nothing more."},
                            {"role": "user", "content": prompt}

                            ], "temperature": 0.7

               }
    
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
