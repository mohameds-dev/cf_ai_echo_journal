from workers import DurableObject, Response, WorkerEntrypoint
import json
import queries
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

class MyDurableObject(DurableObject):
    """
     * The constructor is invoked once upon creation of the Durable Object, i.e. the first call to
     * `DurableObjectStub::get` for a given identifier (no-op constructors can be omitted)
     *
     * @param {DurableObjectState} ctx - The interface for interacting with Durable Object state
     * @param {Env} env - The interface to reference bindings declared in wrangler.jsonc
    """
    def __init__(self, ctx, env):
        super().__init__(ctx, env)
        self.chat_history = []
        self.sql = ctx.storage.sql
        self.sql.exec(queries.SCHEMA_SQL)

    
    async def prompt_llama(self, user_prompt):
        response = await self.env.AI.run('@cf/meta/llama-3.1-8b-instruct', {"prompt": user_prompt})
        response_dict = response.to_py()
        ai_response = response_dict["response"]
        self.sql.exec(
            queries.INSERT_ENTRY, 
            user_prompt, 
            ai_response
        )

        return response_dict
    
    async def get_saved_entries(self):
        cursor = self.sql.exec(queries.SELECT_ALL_ENTRIES)

        return list(cursor)


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
        
        stub = self.env.MY_DURABLE_OBJECT.getByName("foo")

        await stub.prompt_llama("Explain why journaling is good for the brain in one sentence.")
        
        history = await stub.get_saved_entries()

        return Response(
                json.dumps({"history":history}),
                headers={"content-type": "application/json"}
            )
