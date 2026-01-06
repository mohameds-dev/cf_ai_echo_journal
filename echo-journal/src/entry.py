from workers import DurableObject, Response, WorkerEntrypoint
import json
import queries
from prompts import MAIN_PROMPT, UPDATE_PROMPT
from urllib.parse import urlparse

class JournalManager(DurableObject):
    """
     * @param {DurableObjectState} ctx - The interface for interacting with Durable Object state
     * @param {Env} env - The interface to reference bindings declared in wrangler.jsonc
    """
    def __init__(self, ctx, env):
        super().__init__(ctx, env)
        self.sql = ctx.storage.sql
        self.sql.exec(queries.SCHEMA_SQL)
        try:
            row = self.sql.exec(queries.RETRIEVE_CONTEXT).one()
        except Exception:
            row = None
        
        self.running_context = row.to_py().get("value") if row else ""

    async def prompt_llm(self, user_prompt):
        response = await self.env.AI.run('@cf/meta/llama-3.2-3b-instruct', {"prompt": user_prompt})
        return response.to_py().get("response")
    
    async def save_entry_to_history(self, user_prompt, ai_response):
        self.sql.exec(queries.INSERT_ENTRY, user_prompt, ai_response)
    
    async def get_history(self):
        cursor = self.sql.exec(queries.SELECT_ALL_ENTRIES)
        return [row.to_py() for row in cursor]
    
    async def get_text_from_audio(self, audio_bytes):
        if not audio_bytes:
            return ""
        response = await self.env.AI.run('@cf/openai/whisper', {"audio":list(audio_bytes)})
        return response.to_py().get("text")
    
    async def update_context(self, new_prompt):
        self.running_context = await self.prompt_llm(UPDATE_PROMPT.format(self.running_context, new_prompt))
        self.sql.exec(queries.UDPATE_CONTEXT, self.running_context)
    
    async def get_running_context(self):
        return self.running_context
    
    async def clear_history(self):
        self.sql.exec(queries.CLEAR_HISTORY)
        self.sql.exec(queries.CLEAR_CONTEXT)
        self.running_context = ""


"""
* @param {Request} request - The request submitted to the Worker from the client
* @param {Env} env - The interface to reference bindings declared in wrangler.jsonc
* @param {ExecutionContext} ctx - The execution context of the Worker
* @returns {Promise<Response>} The response to be sent back to the client
"""
class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = urlparse(request.url).path
        if path == "/favicon.ico":
            return Response("Not Found", status=404)
        
        stub = self.env.JOURNAL_MANAGER.getByName("main_history")

        if path == "/clear":
            await stub.clear_history()
            return Response("History cleared", status=200)
        
        elif path == "/recording":
            return await self.handle_journal_entry(request, stub)
        
        elif path == "/history":
            history = await stub.get_history()
            return Response(
                json.dumps(history),
                headers={"content-type": "application/json"}
            )
        
        return Response("Not Found", status=404)
        
    
    async def handle_journal_entry(self, request, stub):
        audio_bytes = await self.extract_audio_bytes(request)
        transcribed_text = await stub.get_text_from_audio(audio_bytes)
        current_context = await stub.get_running_context()
        ai_response = await stub.prompt_llm(f"""
            {MAIN_PROMPT} 
            {('Keep in mind the following context:\n' + current_context) if current_context else ''}
            {transcribed_text}
            """)
        
        self.ctx.waitUntil(stub.update_context(transcribed_text))
        self.ctx.waitUntil(stub.save_entry_to_history(transcribed_text, ai_response))

        return Response(
                json.dumps({"user_prompt": transcribed_text, "ai_response": ai_response}),
                headers={"content-type": "application/json"}
            )

    async def extract_audio_bytes(self, request):
        request_data = await request.form_data()
        audio_file = request_data.get("file")
        if not audio_file:
            return None
        audio_bytes = await audio_file.bytes()

        return audio_bytes
