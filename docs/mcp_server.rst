MCP Server
==========

The NOSIBLE Search API can be used through an `MCP server <https://github.com/NosibleAI/nosible-mcp/>`_.


Usage
-----

- Log on to `NOSIBLE <https://www.nosible.ai/search-api>`_ and retrieve your API key.

- Using with VSCode

  - Create a ``.vscode/mcp.json`` file in your workspace.
  - Select the ``Add Server`` button to add a template with your own API key for a new server. It should look like this:

  .. code:: json

      {
        "servers": {
          "nosible-demo": {
            "type": "http",
            "url": "https://nosible-mcp.onrender.com/mcp/",
            "headers": {
              "X-Nosible-Api-Key": "YOUR_NOSIBLE_API_KEY_HERE"
            }
          }
        }
      }

- Using with Claude Desktop:

  - Go to ``settings`` -> ``developer`` -> ``Edit config``
  - Open ``claude_desktop_config.json`` and add the following code below, including your API key.

  .. code:: json

      {
        "mcpServers": {
          "nosible-demo": {
            "command": "npx",
            "args": [
              "mcp-remote",
              "https://nosible-mcp.onrender.com/mcp/",
              "--header",
              "X-Nosible-Api-Key:${NOSIBLE_API_KEY}"
            ],
            "env": {
              "NOSIBLE_API_KEY": "YOUR_NOSIBLE_API_KEY_HERE"
            }
          }
        }
      }

- Using with Cursor:

  - Go to ``Cursor Settings`` -> ``MCP & Integrtions`` -> ``New MCP Server``
  - Add this template below, with your own API key.

  .. code:: json

      {
        "mcpServers": {
          "nosible-demo": {
            "type": "http",
            "url": "https://nosible-mcp.onrender.com/mcp/",
            "headers": {
              "X-Nosible-Api-Key": "YOUR_NOSIBLE_API_KEY_HERE"
            }
          }
        }
      }