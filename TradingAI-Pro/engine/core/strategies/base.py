from typing import Protocol, runtime_checkable

@runtime_checkable
class Strategy(Protocol):
    async def evaluate_async(self, data: dict) -> dict: ...
