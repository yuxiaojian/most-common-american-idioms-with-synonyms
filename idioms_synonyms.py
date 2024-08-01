import os
import click
import logging
import json
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from bs4 import BeautifulSoup

# load_dotenv()
ROOT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

# Vector DB path
PERSIST_DIRECTORY = f"{ROOT_DIRECTORY}/idioms-db"

# Embedding model name
# https://docs.trychroma.com/guides/embeddings for supported embeddings
EMBEDDING_MODEL_NAME = "hkunlp/instructor-large"

# The html file from most-common-american-idioms
# https://github.com/xiaolai/most-common-american-idioms/blob/main/Most_Common_American_Idioms.html
IDIOMS_BOOK= "./Most_Common_American_Idioms.html"

# JSON file for parsed info
IDIOMS_JSON= "./idioms.json"

# New HTML with Synonyms's links
UPDATED_IDIOMS_BOOK= "./Most_Common_American_Idioms_With_Synonyms.html"

# Number of synonyms
NUMBER_OF_SYNONYMS = 6

# logging config
logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s", level=logging.INFO
    )

# Function to parse the HTML file and convert it to JSON
def parse_html_to_json(file_path):
    try:
        # Open and read the HTML file
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Initialize a list to store the idioms data
        idioms_data = []
        
        # Find all <h2> tags
        h2_tags = soup.find_all('h2')
        
        for idx, h2 in enumerate(h2_tags, start=1):
            # Remove order number and get the phrase
            phrase = h2.get_text(strip=True).split('. ', 1)[-1].replace('\n', ' ')
            
            interpretation = ""
            examples = []
            
            # Find the next sibling <p> tag that does not have class 'cn' or 'en'
            p_tag = h2.find_next_sibling('p')
            while p_tag and ('cn' in p_tag.get('class', []) or 'en' in p_tag.get('class', [])):
                p_tag = p_tag.find_next_sibling('p')
            
            if p_tag:
                interpretation = p_tag.get_text(strip=True).replace('\n', ' ')
            
            # Find the next <ul> tag for examples
            ul_tag = h2.find_next('ul')
            if ul_tag:
                li_tags = ul_tag.find_all('li')
                for li in li_tags:
                    example = li.find('span', lang='en').get_text(strip=False)
                    example = example.replace('<em>', ' ').replace('</em>', ' ').replace('\n', ' ')
                    #example = li.find('span', lang='en').get_text(strip=True)
                    # Replace <em> tags with spaces
                    
                    examples.append(example)
            
            # Append the data to the list
            idioms_data.append({
                "id": idx,
                "phrase": phrase,
                "interpretation": interpretation,
                "examples": examples
            })
        
        # Convert the list to JSON format
        json_data = json.dumps(idioms_data, ensure_ascii=False, indent=2)
        
        # Write the JSON data to a file
        with open(IDIOMS_JSON, 'w', encoding='utf-8') as json_file:
            json_file.write(json_data)
        
        logging.info("JSON file %s created successfully." % IDIOMS_JSON)
    
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


# Function to parse the JSON file and generate the required lists
def parse_json_to_lists(file_path):
    try:
        # Open and read the JSON file
        with open(file_path, 'r', encoding='utf-8') as file:
            idioms_data = json.load(file)
        
        # Initialize the lists
        documents = []
        metadata = []
        # ids = []
        
        # Process each idiom entry
        for idiom in idioms_data:
            phrase = idiom['phrase']
            interpretation = idiom['interpretation']
            examples = " ".join(idiom['examples'])
            document = f"{phrase}. {interpretation} For examples. {examples}"
            
            documents.append(document)
            metadata.append({"phrase": phrase, "id": str(idiom['id'])})
            #ids.append(f"id{idiom['id']}")
        
        return documents, metadata
    
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


# Function to generate the desired dictionary
def generate_dict_from_query_results(documents, metadata, idioms_collection_instructor):
    result_dict = {}
    
    for i, doc in enumerate(documents):
        result = idioms_collection_instructor.query(query_texts=[doc], n_results=NUMBER_OF_SYNONYMS+1, include=['metadatas', 'distances'])
        related_phrases = [metadata['phrase'] for metadata in result['metadatas'][0][1:]]
        result_dict[metadata[i]['phrase']] = related_phrases
    
    return result_dict

# Function to parse the HTML file and add links
def add_links_to_html(file_path, link_dict):
    try:
        # Open and read the HTML file
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Iterate over the dictionary to add links
        for source_phrase, target_phrases in link_dict.items():
            # Find the <h2> tag with the source phrase
            h2_tag = soup.find('h2', string=lambda text: text and source_phrase in text)
            if h2_tag:
                # Find the corresponding <ul> tag
                ul_tag = h2_tag.find_next('ul')
                if ul_tag:
                    # Create a new paragraph for the links
                    link_paragraph = soup.new_tag('p')
                    link_paragraph.string = "See also: "
                    
                    # Add links to the paragraph
                    for target_phrase in target_phrases:
                        # Find the <h2> tag with the target phrase to get its id
                        target_h2_tag = soup.find('h2', string=lambda text: text and target_phrase in text)
                        if target_h2_tag:
                            target_id = target_h2_tag.get('id')
                            # Create the link
                            link_tag = soup.new_tag('a', href=f'#{target_id}')
                            link_tag.string = target_phrase
                            link_paragraph.append(link_tag)
                            link_paragraph.append(" ")
                    
                    # Insert the link paragraph after the <ul> tag
                    ul_tag.insert_after(link_paragraph)
        
        # Write the modified HTML back to the file
        with open(UPDATED_IDIOMS_BOOK, 'w', encoding='utf-8') as file:
            file.write(str(soup))
        
        logging.info("Links added and HTML file updated successfully.")
    
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


@click.group()
def cli():
    pass

@cli.command()
def parse_html():
    logging.info("Parse the html and create the JSON file")
    # Call the function to parse the HTML file and create the JSON file
    parse_html_to_json(IDIOMS_BOOK)       

@cli.command()
def create_db():
    logging.info("Create a Chroma DB index from the JSON file")
    
    # Call the function to parse the JSON file and generate the lists
    idioms_docs, idioms_metadata = parse_json_to_lists(IDIOMS_JSON)

    # Create ids from idioms_docs
    idiom_ids = list(map(lambda tup: f"id{tup[0]}", enumerate(idioms_docs)))

    # Create the embedding function and load the model
    instructor_ef = embedding_functions.InstructorEmbeddingFunction(model_name=EMBEDDING_MODEL_NAME, device="cpu")

    # Create chroma client 
    chroma_client_persistent = chromadb.PersistentClient(path=PERSIST_DIRECTORY)

    # Create the vector DB
    # Valid options for hnsw:space are "l2", "ip, "or "cosine". The default is "l2" which is the squared L2 norm.
    # https://docs.trychroma.com/guides
    idioms_collection_instructor = chroma_client_persistent.get_or_create_collection(
        name="idioms",
        embedding_function=instructor_ef,
        metadata={"hnsw:space": "cosine"} # l2 is the default
    )

    # Upsert data to the DB
    # It will take up to 10-15 mins
    idioms_collection_instructor.upsert(documents=idioms_docs, metadatas=idioms_metadata, ids=idiom_ids)


@cli.command()
def update_html():
    logging.info("Update the html file with synonyms' links")

    # Call the function to parse the JSON file and generate the lists
    idioms_docs, idioms_metadata = parse_json_to_lists(IDIOMS_JSON)

    # Create the embedding function and load the model
    instructor_ef = embedding_functions.InstructorEmbeddingFunction(model_name=EMBEDDING_MODEL_NAME, device="cpu")

    # Create chroma client 
    chroma_client_persistent = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
    
    # Get the vector DB index
    idioms_collection_instructor = chroma_client_persistent.get_or_create_collection(
        name="idioms",
        embedding_function=instructor_ef,
        metadata={"hnsw:space": "cosine"} # l2 is the default
    )

    # Query the vector DB and generate the link dictionary
    link_dict = generate_dict_from_query_results(idioms_docs, idioms_metadata, idioms_collection_instructor)

    # Call the function to parse the HTML file and add links
    add_links_to_html(IDIOMS_BOOK, link_dict)



def main():
    """
    Main function for the CLI.
    """
    logging.info(f"Starting ... ")
    cli()

if __name__ == '__main__':

    """
    Disabling huggingface/tokenizers parallelism to avoid deadlocks...
    """
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    main()