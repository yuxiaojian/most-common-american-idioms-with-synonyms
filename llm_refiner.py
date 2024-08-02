from openai import OpenAI
import json
import getpass,os

PROMPT_TEMPLATE="""\
Analyze the phrases and synonyms, and return the top 3 to 6 synonyms most similar to '{phrase}' in meanings from \n '{phrase_synonyms}' \n 
Then, you can add 1 to 3 extra synonyms that are more similar. Organise the list from most similar to least similar.
Provide a $JSON_BLOB, as shown between three backticks:
``` 
{{"synonyms":["synonyms-1",...,"synonyms-n"]}}
``` 
Begin! Reminder to ALWAYS respond with a valid json blob. \
"""

GPT_MODEL="gpt-4o-mini"

class OpenAIRefiner:
    """
    Use OpenAI to refine synonyms found from vector DB 
    """
    def __init__(self, logging) -> None:
        if not os.environ.get('OPENAI_API_KEY'):
            os.environ["OPENAI_API_KEY"] = getpass.getpass("OpenAI API Key [sf-]:")
        self.openai_client = OpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        self.prompt_template=PROMPT_TEMPLATE
        self.logging=logging
    
    # Function to send data to GPT-4 and get the top 6 similar phrases
    def __get_top_similar_phrases(self, phrase, two_level_phrases):
        prompt=self.prompt_template.format(phrase=phrase, phrase_synonyms=json.dumps(two_level_phrases, indent=2))
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an English coach to help us find synonyms."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content
        
        # Extract the JSON
        start_index = response_text.find('{')
        end_index = response_text.rfind('}') + 1
        json_string = response_text[start_index:end_index]
        self.logging.info(f"Got a response %s : %s" % (phrase,json_string))

        # Parse the JSON string into a dictionary
        top_phrases = json.loads(json_string)
        
        return top_phrases
    
    # Function to get all two-level mappings for each phrase
    def __get_two_level_phrases(self, synonyms_dict):
        two_level_dict = {}
        for phrase, first_level_phrases in synonyms_dict.items():
            two_level_phrases = set(first_level_phrases)
            for first_level_phrase in first_level_phrases:
                if first_level_phrase in synonyms_dict:
                    two_level_phrases.update(synonyms_dict[first_level_phrase])
            two_level_dict[phrase] = list(two_level_phrases)
        return two_level_dict
    
    # Generate the new synonyms dictionary
    def __generate_new_synonyms_dict(self, synonyms_dict):
        new_synonyms_dict = {}
        two_level_dict = self.__get_two_level_phrases(synonyms_dict)
        
        for phrase, two_level_phrases in two_level_dict.items():
            top_phrases = self.__get_top_similar_phrases(phrase, two_level_phrases)
            new_synonyms_dict[phrase] = top_phrases["synonyms"]
        
        return new_synonyms_dict
    
    # Read synonyms JSON and output a refined JSON
    def synonyms_refiner(self, input_file, output_file):
        with open(input_file, 'r', encoding='utf-8') as file:
            synonyms_dict = json.load(file)

        refined_synonyms_dict = self.__generate_new_synonyms_dict(synonyms_dict)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(refined_synonyms_dict, f, ensure_ascii=False, indent=4)

