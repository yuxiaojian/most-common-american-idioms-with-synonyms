# most-common-american-idioms-with-synonyms

This project is based on [@xiaolai](https://github.com/xiaolai)'s work -  [most-common-american-idioms](https://github.com/xiaolai/most-common-american-idioms). The [most-common-american-idioms](https://github.com/xiaolai/most-common-american-idioms) book is a great tool to learn English idioms. While enjoying the learning experience, it would be even better to have synonyms so we can learn by analogy. This project is designed to enhance the idiom book with synonyms links. 

It uses [Sentence Embedding](https://en.wikipedia.org/wiki/Sentence_embedding) to find synonyms backed by the [Chroma](https://docs.trychroma.com/) Vector DB. Embedding and Vector DB are key elements in Retrieval Augmented Generation (RAG) to retrieve similar documents for more context before feeding into an LLM model. Here it  uses the vector DB to find synonyms. 


## Usage

Copy the *Most_Common_American_Idioms.html* to the current folder. 

1. Install Python dependencies. 
```bash
pip install -r requirements
```

1. (Optional) Parse the html
It will parse *Most_Common_American_Idioms.html* and generate a JSON file for future usages. The repo contains the JSON file up to July 2024. You only need to prase again if the *Most_Common_American_Idioms.html* is updated afterward. 
```bash
python idioms_synonyms.py parse-html
```

2. (Optional) Create the Vector DB index
If the *Most_Common_American_Idioms.html* is update. Please delete the *idioms-db* folder and run this command to create the vector DB again
```bash
python idioms_synonyms.py create-db
```

3. Update the html with synonyms links
This step requires the JSON file and the vector DB. It will create the *Most_Common_American_Idioms_With_Synonyms.html*
```bash
python idioms_synonyms.py update-html
```

4. Copy the *Most_Common_American_Idioms_With_Synonyms.html* back to your local [most-common-american-idioms](https://github.com/xiaolai/most-common-american-idioms) and open it in a browser. 

<p align="center">
  <img src="images/before-after.png">
</p>