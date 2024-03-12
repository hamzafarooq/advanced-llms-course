**Semantic Caching**

Overview<br>
Semantic Caching enhances the efficiency of semantic search operations by caching query results, thereby reducing redundant computations and trips to the LLM for similar queries. This approach speeds up response times, decreases computational load, and minimizes costs. The project utilizes a sentence transformer model for semantic understanding and integrates with the Qdrant vector database for storing and searching embeddings.

Features <br>
Semantic Understanding: Employs the all-mpnet-base-v2 model to encode questions and grasp their semantics effectively. A different encoder can be used during instantiating SemanticCaching class.
Efficient Caching: Caches query results and employs a similarity threshold to determine cache hits, thereby improving response times for similar queries.
