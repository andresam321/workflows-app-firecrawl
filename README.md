# workflows-app-firecrawl

## For your first connector you will be working on Firecrawl -  a webscraping API.
 # You will have to integrate these 6 main actions:
- Scrape
- Batch Scrape
- Extract
- Map
- Search
- Crawl


## Next action items:
Completed - Create a public repo on your Github account called “workflows-app-firecrawl” forking our template
Completed - Set up the connector according to the tutorial
Completed - Create the private app on the Workflows Developer Studio
Start building!
Make sure to update us as soon as you have endpoints ready. If you have any technical questions you can ping me. (edited) 


## Features Description
Scrape: scrapes a URL and get its content in LLM-ready format (markdown, structured data via LLM Extract, screenshot, html)
Crawl: scrapes all the URLs of a web page and return content in LLM-ready format
Map: input a website and get all the website urls - extremely fast
Search: search the web and get full content from results
Extract: get structured data from single page, multiple pages or entire websites with AI.

## ⚙️ UI Options & Field Config Guidelines

Here are some useful notes for configuring fields in your `schema.json` when building actions in Dev Studio:

### ✅ Checkboxes
- To render a checkbox, set:
  ```json
  {
    "id": "exampleField",
    "type": "boolean",
    "label": "This is the checkbox label",
    "validation": {
      "required": true
    }
  }