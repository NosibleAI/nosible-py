.. image:: _static/sticker.png
   :align: right
   :width: 190px
   :alt: Nosible logo
   :class: rounded-image

NOSIBLE Client Documentation
============================

Welcome to the NOSIBLE Client package! This documentation will give you an in-depth overview of the NOSIBLE Search
API, and show you how to harness the power of the NOSIBLE Search Engine.

Our mission is to be the undisputed **BEST** source of data for artificial intelligence agents
operating in the financial services sector. Engineered for quant funds and financial innovators
alike, Nosible makes it possible to build AI agents that are grounded in high-quality, verified
data.

Features
========

Search Capabilities
-------------------

- **Algorithm Selection:** You can switch between verbatim, lexical, semantic, hybrid, knowledge,
  agentic, and bespoke finance-optimized search algorithms, depending on your use case.

- **Query Expansion:** You can submit up to 10 related search terms in one shot to retrieve
  higher-quality search results. We will treat that as one API request, so it's a 10-for-1 special.

- **Native Pre-filtering:** You can filter your search results by specific publishers, date
  ranges, languages, and more without sacrificing search quality. We natively support
  pre-filtering.

- **Bulk Search:** You can retrieve up to 10,000 relevant search results for any search term
  using any search algorithm and filter. All of your search results will be securely hosted
  on S3.

----

Scale and Coverage
------------------

- **25x Larger Than Wikipedia:** Nosible has indexed over 500 million content webpages from
  across the web. Our index contains billions of embeddings and hundreds of billions of
  tokens of text.

- **Over 10,000 Websites:** Nosible is indexing historical and breaking news from over
  10,000 media websites around the world. Every domain we whitelist is stringently vetted.

- **Non-news Content:** Nosible is rapidly expanding coverage of non-news content from the web,
  including all asset manager websites, public company blogs, financial regulators, and more.

- **Over 75 Languages:** Nosible has content in over 75 languages, including - but not limited
  to - Mandarin, Arabic, Hindi, Japanese, German, Spanish, French, Bengali, Portuguese, and more.

----

Features for Quants
-------------------

- **Sentiments:** Get curated datasets and data feeds of sentiment scores for any entity
  (people, places, or companies) worldwide, going back to 1998, with commercial rights.

- **Summaries:** Get summaries of all media coverage for any entity in the world dating
  back to 1998. It's time that you ran your backtest on the signal—not the noise.

- **Event Feeds:** You can also get summaries and sentiments for current and historical
  events that affected markets, including geopolitical events such as elections and crashes.

- **Real-time Support:** Everything we build is designed to work in the context of a
  historical backtest and a live-trading environment. Our datafeeds update hourly.

If you are looking to build AI products, agents, and AI-driven investment strategies,
the Nosible Search API is for you.

----

.. toctree::
   :maxdepth: 4
   :caption: User Guide
   :hidden:

   getting_started
   configuration
   rate_limits

API reference
-------------

.. autosummary::
   :toctree: api
   :caption: API Reference

   nosible.Nosible
   nosible.Result
   nosible.ResultSet
   nosible.Search
   nosible.SearchSet
   nosible.WebPageData
   nosible.Snippet
   nosible.SnippetSet