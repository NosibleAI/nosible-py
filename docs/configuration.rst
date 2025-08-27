Configuration
=============

Configure your search to get the most out of the NOSIBLE Search Engine. You can tailor both the scope and behavior of
your queries by adjusting the parameters below. Whether you need broad recall or very focused, precise results,
the settings in `search parameters <search_parameters_>`_ let you balance speed, relevance, and depth.

.. _search_parameters:

🎛️ Search Parameters
--------------------

question
~~~~~~~~

The primary search query you want answered.
    - **Type**: ``str``
    - **Default**: (required)
    - **Example**: ``"Hedge funds seek to expand into private credit"``

expansions
~~~~~~~~~~

Up to 10 semantically/lexically related queries to boost recall - only counts as part of one request.
    - **Type**: ``List[str]``
    - **Default**: ``[]``
    - **Maximum**: 10
    - **Example**: ``["What drives Blackstone’s decision to boost exposure to private credit asset classes?", ...]``

n_results
~~~~~~~~~

Maximum number of results to return.
    - **Type**: ``int``
    - **Default**:
        - Search: ``100``
        - Bulk search: ``10_000``
    - **Maximum**:
        - Search: ``100``
        - Bulk search: ``10_000``
    - **Example**: ``100``

n_probes
~~~~~~~~

The number of index shards to probe. More shards will mean better recall, but slower query speeds.
    - **Type**: ``int``
    - **Default**: ``300``
    - **Maximum**:
        - Search: ``30``
        - Bulk search: ``300``
    - **Example**: ``30``

n_contextify
~~~~~~~~~~~~

Number of context tokens to include per result.
    - **Type**: ``int``
    - **Default**: ``128``
    - **Maximum**: ``1024``
    - **Example**: ``512``

algorithm
~~~~~~~~~

This parameter allows us to control the type of search algorithm used when scoring and ordering search results.
    - **Type**: ``str``
    - **Default**: ``hybrid-3``
    - **Example**: ``hybrid-2``

min_similarity
~~~~~~~~~~~~~~

Results must have at least this similarity score.
    - **Type**: ``float``
    - **Default**: ``0``
    - **Example**: ``0.65``

must_include
~~~~~~~~~~~~

Only results mentioning these strings will be included.
    - **Type**: ``list of str``
    - **Default**: ``None``
    - **Example**: ``["String 1", "String 2"]``

must_exclude
~~~~~~~~~~~~

Any result mentioning these strings will be excluded.
    - **Type**: ``list of str``
    - **Default**: ``None``
    - **Example**: ``["String 1", "String 2"]``

autogenerate_expansions
~~~~~~~~~~~~~~~~~~~~~~~

Do you want to generate expansions automatically using an LLM? Note that you will need to provide an LLM API key.
    - **Type**: ``bool``
    - **Default**: ``False``
    - **Example**: ``True``

publish_start
~~~~~~~~~~~~~

Start date for when the document was published (ISO format).
    - **Type**: ``ISO formatted date string``
    - **Default**: None
    - **Example**: ``"2020-10-01"``

publish_end
~~~~~~~~~~~

End date for when the document was published (ISO format).
    - **Type**: ``ISO formatted date string``
    - **Default**: None
    - **Example**: ``"2025-10-01"``

visited_start
~~~~~~~~~~~~~

Start date for when the document was visited by NOSIBLE (ISO format).
    - **Type**: ``ISO formatted date string``
    - **Default**: None
    - **Example**: ``"2024-10-01"``

visited_end
~~~~~~~~~~~

End date for when the document was visited by NOSIBLE (ISO format).
    - **Type**: ``ISO formatted date string``
    - **Default**: None
    - **Example**: ``"2025-10-01"``

certain
~~~~~~~

Whether we are 100% certain of the date.
    - **Type**: ``bool``
    - **Default**: None
    - **Example**: ``True``

include_netlocs
~~~~~~~~~~~~~~~

List of netlocs (domains) to include in the search.
    - **Type**: ``List[str]``
    - **Default**: None
    - **Maximum**: 50
    - **Example**: ``["bbc.com", "cnn.com"]``

exclude_netlocs
~~~~~~~~~~~~~~~

List of netlocs (domains) to exclude from the search.
    - **Type**: ``List[str]``
    - **Default**: None
    - **Maximum**: 50
    - **Example**: ``["bbc.com", "cnn.com"]``

include_companies
~~~~~~~~~~~~~~~~~

Companies to include in the search.
    - **Type**: ``List[str]``
    - **Default**: None
    - **Maximum**: 50
    - **Example**: ``["/m/09rh_", "/m/045c7b"]``

exclude_companies
~~~~~~~~~~~~~~~~~

Companies to exclude from the search.
    - **Type**: ``List[str]``
    - **Default**: None
    - **Maximum**: 50
    - **Example**: ``["/m/09rh_", "/m/045c7b"]``

include_docs
~~~~~~~~~~~~

Document IDs to include in the search.
    - **Type**: ``List[str]``
    - **Default**: None
    - **Maximum**: 50
    - **Example**: ``["SMkZ5HuEBYmevqbYHm-G5N36z1h...", "H5FIc-yuUDU4deFtowSPDEbM..."]``

exclude_docs
~~~~~~~~~~~~

Document IDs to exclude from the search.
    - **Type**: ``List[str]``
    - **Default**: None
    - **Maximum**: 50
    - **Example**: ``["SMkZ5HuEBYmevqbYHm-G5N36z1h...", "H5FIc-yuUDU4deFtowSPDEbM..."]``

brand_saftey
~~~~~~~~~~~~

Whether it is safe, sensitive, or unsafe to advertise on this content.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Safe"``

language
~~~~~~~~

Allows you to pass in a language that all search results must be written in. We support over 75 languages including the difficult ones such as Japanese Mandarin and Arabic.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"en"``

continent
~~~~~~~~~

The continent you would like your search results to be refined to.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Africa"``

region
~~~~~~

The geographic region you would like your search results to be refined to.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Central Africa"``

country
~~~~~~~

The country you would like your search results to be refined to.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Denmark"``

sector
~~~~~~

The GICS sector you would like your search results to be refined to.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Information Technology"``

industry_group
~~~~~~~~~~~~~~

The GICS industry group you would like your search results to be refined to.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Banks"``

industry
~~~~~~~~

The GICS industry you would like your search results to be refined to.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Containers & Packaging"``

sub_industry
~~~~~~~~~~~~

The GICS sub-industry you would like your search results to be refined to.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Air Freight & Logistics"``

iab_tier_1
~~~~~~~~~~

The tier 1 IAB category you would like your search results to be refined to.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Attractions"``

iab_tier_2
~~~~~~~~~~

The tier 2 IAB category you would like your search results to be refined to.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Field Hockey"``

iab_tier_3
~~~~~~~~~~

The tier 3 IAB category you would like your search results to be refined to.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Concept Cars"``

iab_tier_4
~~~~~~~~~~

The tier 4 IAB category you would like your search results to be refined to.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Auto Rentals"``

instruction
~~~~~~~~~~~

Instrucion to use with the search query.
    - **Type**: ``str``
    - **Default**: None
    - **Example**: ``"Retrieve semantically similar text."``

.. _search_algorithms:

🤖 Search Algorithms
--------------------

The types of algorithms to use when scoring and ordering search results.

lexical
~~~~~~~

- Perform a standard keyword search using BM25 scoring.

string
~~~~~~

- Runs an exact-match full-text search, returning only documents that contain your query verbatim.

hybrid-1
~~~~~~~~

- First executes a semantic search to capture conceptual matches, then refines the results with a lexical search.

hybrid-2
~~~~~~~~

- First use lexical search to narrow results, then refines the results with a semantic search.

hybrid-3
~~~~~~~~

- Our most cutting edge search algorithm. Beats everything else.

🌐 Change LLM Base URL
----------------------

The LLM endpoint is used to generate expansions for searches and calculate sentiment for search results, and by default
it is set to use OpenRouter. However, **we support any endpoint that supports openai**. If you want to use a different
endpoint, you can do so by changing the client argument ``openai_base_url``:

.. code:: python

   from nosible import Nosible

   client = Nosible(
       nosible_api_key="basic|abcd1234...",
       llm_api_key="sk-...",
       openai_base_url="https://api.openrouter.ai/v1"
   )

🗣️ Supported Languages
----------------------

Here is a list of all languages currently supported by NOSIBLE, and their corresponding language codes that you will
use when you filter.

.. list-table:: Supported Languages and Codes
   :header-rows: 1

   * - Language
     - Code
   * - Afrikaans
     - af
   * - Amharic
     - am
   * - Arabic
     - ar
   * - Assamese
     - as
   * - Azerbaijani
     - az
   * - Belarusian
     - be
   * - Bulgarian
     - bg
   * - Bengali
     - bn
   * - Breton
     - br
   * - Bosnian
     - bs
   * - Catalan
     - ca
   * - Czech
     - cs
   * - Welsh
     - cy
   * - Danish
     - da
   * - German
     - de
   * - Greek
     - el
   * - English
     - en
   * - Esperanto
     - eo
   * - Spanish
     - es
   * - Estonian
     - et
   * - Basque
     - eu
   * - Persian
     - fa
   * - Finnish
     - fi
   * - French
     - fr
   * - Western Frisian
     - fy
   * - Irish
     - ga
   * - Scottish Gaelic
     - gd
   * - Galician
     - gl
   * - Gujarati
     - gu
   * - Hausa
     - ha
   * - Hebrew
     - he
   * - Hindi
     - hi
   * - Croatian
     - hr
   * - Hungarian
     - hu
   * - Armenian
     - hy
   * - Indonesian
     - id
   * - Icelandic
     - is
   * - Italian
     - it
   * - Japanese
     - ja
   * - Javanese
     - jv
   * - Georgian
     - ka
   * - Kazakh
     - kk
   * - Khmer
     - km
   * - Kannada
     - kn
   * - Korean
     - ko
   * - Kurdish
     - ku
   * - Kyrgyz
     - ky
   * - Latin
     - la
   * - Lao
     - lo
   * - Lithuanian
     - lt
   * - Latvian
     - lv
   * - Malagasy
     - mg
   * - Macedonian
     - mk
   * - Malayalam
     - ml
   * - Mongolian
     - mn
   * - Marathi
     - mr
   * - Malay
     - ms
   * - Burmese
     - my
   * - Nepali
     - ne
   * - Dutch
     - nl
   * - Norwegian
     - no
   * - Oromo
     - om
   * - Oriya
     - or
   * - Panjabi
     - pa
   * - Polish
     - pl
   * - Pashto
     - ps
   * - Portuguese
     - pt
   * - Romanian
     - ro
   * - Russian
     - ru
   * - Sanskrit
     - sa
   * - Sindhi
     - sd
   * - Serbo-Croatian
     - sh
   * - Sinhala
     - si
   * - Slovak
     - sk
   * - Slovenian
     - sl
   * - Somali
     - so
   * - Albanian
     - sq
   * - Serbian
     - sr
   * - Sundanese
     - su
   * - Swedish
     - sv
   * - Swahili
     - sw
   * - Tamil
     - ta
   * - Telugu
     - te
   * - Thai
     - th
   * - Tagalog
     - tl
   * - Turkish
     - tr
   * - Uyghur
     - ug
   * - Ukrainian
     - uk
   * - Urdu
     - ur
   * - Uzbek
     - uz
   * - Vietnamese
     - vi
   * - Xhosa
     - xh
   * - Yiddish
     - yi
   * - Chinese
     - zh

