"""
WebSocket endpoint for real-time evaluation updates
TODO: Implement WebSocket connection for streaming evaluation results
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.core.runner import run_evaluation
from app.models.models import EvaluationRequest

router = APIRouter()

@router.websocket("/ws/evaluate")
async def websocket_evaluation(websocket: WebSocket, request: EvaluationRequest):
    await websocket.accept()
    
    try:
        async for update in run_evaluation(blueprint=request.blueprint, traces=request.traces):
            await websocket.send_text(update)

        await websocket.send_text("Evaluation complete!") 

    except WebSocketDisconnect:
        print("Client disconnected.")

#@router.websocket("ws/refinement")