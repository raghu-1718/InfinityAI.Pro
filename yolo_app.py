from fastapi import FastAPI, File, UploadFile
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import io

app = FastAPI(title="YOLO Object Detection API")

# Load YOLO model
model = YOLO('yolov8n.pt')

@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    """
    Detect objects in uploaded image
    """
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Run inference
        results = model(img)

        # Process results
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = box.conf[0].cpu().numpy()
                class_id = int(box.cls[0].cpu().numpy())
                class_name = model.names[class_id]

                detections.append({
                    "class": class_name,
                    "confidence": float(confidence),
                    "bbox": [float(x1), float(y1), float(x2), float(y2)]
                })

        return {"detections": detections}

    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "YOLO Object Detection API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)