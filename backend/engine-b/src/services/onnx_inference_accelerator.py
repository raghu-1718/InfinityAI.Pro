"""
InfinityAI.Pro — ONNX Inference Accelerator Service Re-Export
"""
try:
    from ..inference.onnx_inference_accelerator import ONNXInferenceAccelerator, ONNX_ACCELERATOR
except Exception:
    from src.inference.onnx_inference_accelerator import ONNXInferenceAccelerator, ONNX_ACCELERATOR

__all__ = ["ONNXInferenceAccelerator", "ONNX_ACCELERATOR"]
