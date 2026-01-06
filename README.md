# cf_ai_echo_journal

### Project structure

- `src/entry.py`: the main python logic for the API
- `src/queries.py`: sql queries used in `entry.py`, placed in a separate file for better readability and SOC
-  `public`: Where the frontend assets live


### Running the project (tested using Ubuntu Linux)

0. Ensure to have:
    -  a recent version of node and npm (relative to the time of this project's creation)
    -  GLIBC 2.34+ (found in Ubuntu 22.04+, Debian 12+, or macOS/Windows).
1. Install uv. You may use this command: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Restart your shell.
3. Enter the project directory `cd echo-journal`
4. Use `uv sync` which will create the virtual environment inside `.venv` using `pyproject.toml`
5. Activate the environment
   1. Use `. ./.venv/bin/activate` to activate the venv in the current shell
   2. If you're getting unresolved library errors and squiggly lines, make sure the IDE has selected the `.venv` as its interpreter
6. **Important**: Authenticate with Cloudflare for AI features to work: Run `npx wrangler login` and follow the prompts.
7. Run the project using this command: `npm run dev`
   - **Optional**: if you wish to run on remote instead of local, use `npm run dev -- --remote`.
8. **Deployment**: 
   - To deploy, use `npx wrangler deploy`
   - Make sure to have `workers_dev: true` in `wrangler.jsonc` to be able to access the endpoint
   - The default deployment url is at `https://echo-journal.<your-subdomain>.workers.dev/`

### Troubleshooting

- A local SQLite database is created by default. To delete it and start fresh, remove the hidden `.wrangler` folder. You can use this command: `rm -rf .wrangler`


### Architectural notes & technical descisions

- The Durable Object, which is used for data persistence, is named "main_history" is hard-coded just for this proof of concept. In real-world applications, it would be generated using the user ID, which is only possible in an application with Auth set up.


### 📖 Documentation
https://developers.cloudflare.com/workers

### 🐛 Report an Issue
https://github.com/cloudflare/workers-sdk/issues/new/choose

### 💬 Community
https://discord.cloudflare.com


