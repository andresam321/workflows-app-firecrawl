# workflows-app-firecrawl

## About This Connector
This integration was created as part of the Stacksync Connector Development Programme, focusing on building production-ready workflows using external APIs. This connector integrates Firecrawl, a web scraping API, into the Stacksync platform by implementing key actions like Scrape, Batch Scrape, Extract, Map, Search, and Crawl.

## 🔥 Firecrawl Connector Overview

This connector integrates with Firecrawl — a powerful web scraping API — to support the following actions:

### 🚀 Main Actions:
- **Scrape** – Scrapes a single URL and returns content in LLM-ready formats (Markdown, structured data, screenshot, HTML).
- **Batch Scrape** – (To be implemented) Scrapes multiple URLs at once.
- **Extract** – Extracts structured data from a single page, multiple pages, or entire sites using AI.
- **Map** – Inputs a website and maps out all its internal URLs. Super fast.
- **Search** – Queries the web and retrieves full content from the search results.
- **Crawl** – Crawls all links on a page and returns their content in LLM-ready formats.

---

## ⚙️ UI Options & Field Config Guidelines (for Dev Studio)

These notes are for internal use when building actions with Dev Studio.

### ✅ Checkboxes
- To render a checkbox, just set the field's `type` to `"boolean"` and define the label:
  ```json
  {
    "id": "exampleField",
    "type": "boolean",
    "label": "Enable this option",
    "validation": {
      "required": true
    }
  }
