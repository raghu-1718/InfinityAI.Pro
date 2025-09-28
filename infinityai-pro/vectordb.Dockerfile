FROM chromadb/chroma:latest

# Set environment variables
ENV CHROMA_SERVER_HOST=0.0.0.0
ENV CHROMA_SERVER_HTTP_PORT=8000

# Create data directory
RUN mkdir -p /chroma

# Expose port
EXPOSE 8000

# Run ChromaDB
CMD ["chroma", "run", "--host", "0.0.0.0", "--port", "8000", "--path", "/chroma"]