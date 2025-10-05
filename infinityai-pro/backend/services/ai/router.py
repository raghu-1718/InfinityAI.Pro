"""AI Router service"""
class AIRouter:
    async def route_request(self, request):
        return {"routed": True, "request": request}