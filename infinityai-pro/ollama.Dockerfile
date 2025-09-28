FROM ollama/ollama:latest

# Set environment variables
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_PORT=11434

# Create data directory
RUN mkdir -p /root/.ollama

# Expose port
EXPOSE 11434

# Start Ollama
CMD ["ollama", "serve"]