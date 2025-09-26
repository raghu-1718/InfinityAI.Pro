FROM chromadb/chroma:latest

# Set environment variables
ENV CHROMA_HOST=0.0.0.0
ENV CHROMA_PORT=8000

# Expose the port
EXPOSE 8000

# Start ChromaDB
CMD ["chroma", "run", "--host", "0.0.0.0", "--port", "8000", "--path", "/data"]