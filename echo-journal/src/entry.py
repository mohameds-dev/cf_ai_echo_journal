from workers import DurableObject, Response, WorkerEntrypoint
import json
import queries
from prompts import MAIN_PROMPT, UPDATE_PROMPT

"""
 * Welcome to Cloudflare Workers! This is your first Durable Objects application.
 *
 * - Run `npm run dev` in your terminal to start a development server
 * - Open a browser tab at http://localhost:8787/ to see your Durable Object in action
 * - Run `npm run deploy` to publish your application
 *
 * Learn more at https://developers.cloudflare.com/durable-objects
"""

"""
 * Env provides a mechanism to reference bindings declared in wrangler.jsonc within Python
 *
 * @typedef {Object} Env
 * @property {DurableObjectNamespace} MY_DURABLE_OBJECT - The Durable Object namespace binding
"""

class JournalManager(DurableObject):
    """
     * The constructor is invoked once upon creation of the Durable Object, i.e. the first call to
     * `DurableObjectStub::get` for a given identifier (no-op constructors can be omitted)
     *
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
        cursor = await self.sql.exec(queries.SELECT_ALL_ENTRIES)
        return [dict(row) for row in cursor]
    
    async def get_text_from_audio(self, audio_bytes):
        response = await self.env.AI.run('@cf/openai/whisper', {"audio":list(audio_bytes)})
        return response.to_py().get("text")
    
    async def update_context(self, new_prompt):
        self.running_context = await self.prompt_llm(UPDATE_PROMPT.format(self.running_context, new_prompt))
        self.sql.exec(queries.UDPATE_CONTEXT, self.running_context)
    
    async def get_running_context(self):
        return self.running_context


"""
* This is the standard fetch handler for a Cloudflare Worker
*
* @param {Request} request - The request submitted to the Worker from the client
* @param {Env} env - The interface to reference bindings declared in wrangler.jsonc
* @param {ExecutionContext} ctx - The execution context of the Worker
* @returns {Promise<Response>} The response to be sent back to the client
"""
class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if "/favicon.ico" in request.url:
            return Response("Not Found", status=404)
        
        if "recording" not in request.url:
            return Response("Not Found", status=404)
        
        stub = self.env.JOURNAL_MANAGER.getByName("main_history")

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
