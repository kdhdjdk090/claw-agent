# AI & Machine Learning Skill Pack

## LLM Integration
- **API Patterns**: Retry with exponential backoff + jitter. Stream for UX. Cache deterministic calls
- **Prompt Engineering**: System message for persona/rules. User message for task. Few-shot examples
- **Structured Output**: JSON mode or function calling. Validate with Zod/Pydantic after generation
- **Cost Control**: Route easy tasks to smaller models. Cache prompt prefixes. Batch where possible
- **Token Management**: Track usage per request. Set per-user/per-request budgets. Alert on spikes

## RAG (Retrieval-Augmented Generation)
- **Chunking**: 512-1024 tokens. Overlap 10-20%. Respect document structure (headers, sections)
- **Embeddings**: text-embedding-3-small for cost, text-embedding-3-large for quality
- **Vector Store**: Pinecone, Qdrant, Weaviate, or pgvector for small scale
- **Retrieval**: Hybrid search (semantic + keyword). Re-rank top results. Cite sources
- **Evaluation**: Relevance, faithfulness, answer correctness. RAGAS framework

## Agent Patterns
- **Tool Use**: Define tools with clear descriptions. Validate tool inputs. Handle errors gracefully
- **Planning**: Decompose complex tasks into steps. Re-plan if a step fails
- **Memory**: Short-term (conversation), long-term (vector store), working (scratchpad)
- **Safety**: Sandboxed execution. Human-in-the-loop for destructive actions. Input sanitization

## Model Fine-Tuning
- **When**: Consistent formatting needs, domain-specific behavior, cost optimization
- **Data**: 50-100 high-quality examples minimum. Diverse, representative, validated
- **Process**: Baseline eval → Format data → Train → Eval → Compare → Deploy or iterate
- **Eval-First**: Define metrics BEFORE training. Automated eval suite runs on every version

## MLOps
- **Model Registry**: Version models with metadata, metrics, lineage. MLflow or Weights & Biases
- **Deployment**: A/B testing with traffic splitting. Shadow mode for new models
- **Monitoring**: Input drift, output drift, latency, error rate, cost per prediction
- **Retraining**: Trigger on drift detection or schedule. Automated pipeline with rollback
