from functools import wraps

def activity(func):
    @wraps(func)
    async def reset_durable_object_timer_on_activity(self, *args, **kwargs):
        self.reset_cleanup_timer()
        return await func(self, *args, **kwargs)
    return reset_durable_object_timer_on_activity

import sys

def log_exception(exception, custom_message=None):
    func_name = sys._getframe(1).f_code.co_name
    print(f"--- [ERROR caught at: {func_name}] ---")
    
    if custom_message:
        print(f"Context: {custom_message}")
    
    print(f"Details: {type(exception).__name__}: {str(exception)}")
    print("----------------------------")