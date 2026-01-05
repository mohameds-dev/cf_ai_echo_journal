# cf_ai_echo_journal

### Project structure

- `src/entry.py`: the main python logic for the API
- `src/queries.py`: sql queries used in `entry.py`, placed in a separate file for better readability and SOC
-  `public`: Where the frontend assets live


### To run the project locally

0. Ensure to have a recent version of node and npm (relative to the time of this project's creation)
1. Install uv. You may use this command: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Enter the project directory `echo-journal`
3. Use `uv sync` which will create the `.venv` using `pyproject.toml`
4. Activate the `.venv` (your IDE should recognize it to avoid unresolved library errors and squiggly lines)
5. Run the project using this command: `npm run dev`

### Troubleshooting

- To reset the local storage, remove the hidden `.wrangler` folder. You can use this command: `rm -rf .wrangler`


### 📖 Documentation
https://developers.cloudflare.com/workers

### 🐛 Report an Issue
https://github.com/cloudflare/workers-sdk/issues/new/choose

### 💬 Community
https://discord.cloudflare.com


