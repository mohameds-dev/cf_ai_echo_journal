from functools import wraps
import struct
import math

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


def is_valid_speech(audio_bytes):
        if not audio_bytes or len(audio_bytes) < 2000:
            return False

        try:
            sample_count = len(audio_bytes) // 2
            samples = struct.unpack(f"{sample_count}h", audio_bytes[:sample_count * 2])
            sum_squares = sum(s**2 for s in samples)
            rms = math.sqrt(sum_squares / len(samples))

            return rms > 300 

        except Exception as e:
            log_exception(e)
            return True
