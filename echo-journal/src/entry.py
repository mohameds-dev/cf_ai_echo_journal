from workers import DurableObject, Response, WorkerEntrypoint
import json
import queries
from prompts import MAIN_PROMPT, UPDATE_PROMPT
from urllib.parse import urlparse
from utils import activity, log_exception
import time

class JournalManager(DurableObject):
    """
     * @param {DurableObjectState} ctx - The interface for interacting with Durable Object state
     * @param {Env} env - The interface to reference bindings declared in wrangler.jsonc
    """
    def __init__(self, ctx, env):
        super().__init__(ctx, env)
        self.storage = ctx.storage
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
    
    @activity
    async def save_entry_to_history(self, user_prompt, ai_response):
        self.sql.exec(queries.INSERT_ENTRY, user_prompt, ai_response)
    
    @activity
    async def get_history(self):
        cursor = self.sql.exec(queries.SELECT_ALL_ENTRIES)
        return [row.to_py() for row in cursor]
    
    async def get_text_from_audio(self, audio_bytes):
        if not audio_bytes:
            return ""
        try:
            response = await self.env.AI.run('@cf/openai/whisper', {"audio":list(audio_bytes)})
            return response.to_py().get("text")
        except Exception as e:
            log_exception(e)
            return ""
    
    async def update_context(self, new_prompt):
        self.running_context = await self.prompt_llm(UPDATE_PROMPT.format(self.running_context, new_prompt))
        self.sql.exec(queries.UPDATE_CONTEXT, self.running_context)
    
    async def get_running_context(self):
        return self.running_context
    
    async def clear_history(self):
        self.sql.exec(queries.CLEAR_HISTORY)
        self.sql.exec(queries.CLEAR_CONTEXT)
        self.running_context = ""

    def reset_cleanup_timer(self):
        SECOND = 1000
        SEVEN_DAYS_IN_SEC = 7 * 24 * 60 * 60 
        new_expiration_time = (int(time.time()) + SEVEN_DAYS_IN_SEC) * SECOND
        self.storage.setAlarm(new_expiration_time)

    async def alarm(self):
        await self.storage.deleteAll()
        self.sql.exec(queries.SCHEMA_SQL)
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
        
        stub = self.get_stub(request)

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
        if not audio_bytes:
            return Response("No audio data provided.", status=400)
        
        try:
            transcribed_text = await stub.get_text_from_audio(audio_bytes)
            current_context = await stub.get_running_context()
            ai_response = await stub.prompt_llm(f"""
                {MAIN_PROMPT} 
                {(f'Keep in mind the following context:\n{current_context}') if current_context else ''}
                {transcribed_text}
                """)
            
            self.ctx.waitUntil(stub.update_context(transcribed_text))
            self.ctx.waitUntil(stub.save_entry_to_history(transcribed_text, ai_response))

            return Response(
                    json.dumps({"user_prompt": transcribed_text, "ai_response": ai_response}),
                    headers={"content-type": "application/json"}
                )
        
        except Exception as e:
            log_exception(e)
            return Response("Error occurred. Please try again later.", status=500)

    

    async def extract_audio_bytes(self, request):
        try:
            request_data = await request.form_data()
            audio_file = request_data.get("file")
            audio_bytes = await audio_file.bytes()

            return audio_bytes
        except Exception as e:
            print("Exception caught at extract_audio_bytes : " + str(e))
            return None

    def get_stub(self, request):
        user_id = request.headers.get("EchoJournal-User-ID") or "anonymous_default"
        obj_id = self.env.JOURNAL_MANAGER.idFromName(user_id)
        stub = self.env.JOURNAL_MANAGER.get(obj_id)

        return stub
