## 🎙️ Echo Journal

Echo Journal is a stateful, voice-first AI journaling application built on the Cloudflare edge. It transforms spoken thoughts into structured reflections while maintaining a persistent "brain" that remembers the conversation history.

This was built as part of an optional Cloudflare internship application assignment.

🧠 The Core Concept
- Voice-to-Insight Pipeline: User records audio → Transcribed via Whisper → Passed to Llama 3.2 (3B) using the running context → Concise, factual reflection returned to user.
- Stateful Intelligence: A Durable Object acts as a long-lived state container with its own database and maintained context, ensuring your journal isn't just a series of isolated entries.

---

### Architecture overview

- **Frontend**
  - Minimal HTML/CSS/JS served by the Worker
  - Handles basic interaction and audio input
  - Sends requests to the API endpoint

- **Cloudflare Worker (Python)**
  - Entry point for requests
  - Orchestrates prompt construction
  - Interfaces with the Durable Object

- **Durable Object**
  - Stores evolving AI state
  - Uses SQLite for persistence
  - Represents a single logical “memory instance”


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

- **Prototyping Note on Data Isolation**: For this proof-of-concept, the application uses a single Durable Object instance to manage state.
   - Current State: Data is persisted across all sessions. This means multiple users currently share the same "hidden context" and history.
   - Production Path: In a real-world deployment, I would implement Multi-tenancy by dynamically creating a unique Durable Object ID for each authenticated User ID. This would ensure strict data isolation where every user has their own private "brain" and history.
- **Using the smaller Llama 3.2 (20B) instead of bigger models**: I opted for a smaller, more "blunt" model specifically to reduce hallucination drift. While larger models (like 70B) often try to invent complex narratives or characters to be "helpful," the 3B model is more literal and factual. It fits the use case perfectly by strictly summarizing the user's state without adding creative or imagined layers.




