# scrum-guide-rag

Primer proyecto para construir y entender un RAG local en Python.

## Idea

Un RAG tiene cuatro piezas:

1. **Carga**: leer los documentos fuente.
2. **Chunking**: partirlos en fragmentos recuperables.
3. **Indexado**: convertir fragmentos a embeddings y guardarlos en una base vectorial.
4. **Chat**: buscar fragmentos relevantes y pedirle al modelo que responda usando solo ese contexto.

Este proyecto usa:

- Python
- LangChain
- Chroma como vector store local
- Ollama como runtime local
- `nomic-embed-text` para embeddings
- `llama3.2` para responder

## Preparacion

Instala Ollama y descarga los modelos:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

Crea un entorno e instala dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

La guia ya esta copiada en `data/2020-Scrum-Guide-Spanish-Latin-South-American.pdf`.
El cargador tambien acepta otros PDF, `.txt` o Markdown que agregues dentro de `data/`.

## Uso

Indexar documentos:

```bash
python3 -m scrum_rag.ingest
```

El indexado borra y reconstruye `chroma_db/` para evitar mezclar fragmentos viejos con una version nueva.

Chatear:

```bash
python3 -m scrum_rag.chat
```

Abrir el chat web:

```bash
python3 -m uvicorn scrum_rag.web.app:app --reload
```

Luego abre `http://127.0.0.1:8000`.

Inspeccionar que fragmentos recupera una pregunta:

```bash
python3 -m scrum_rag.search "oopsla"
```

Evaluar el RAG contra el golden dataset:

```bash
python3 -m scrum_rag.evaluate --retrieval-only
python3 -m scrum_rag.evaluate
```

El primer comando mide retrieval sin llamar al modelo generativo. El segundo ejecuta el flujo completo y guarda reportes en `eval/reports/`.

Comandos dentro del chat:

- `/sources`: muestra las fuentes de la ultima respuesta
- `/exit`: salir

## Experimentos sugeridos

- Cambiar `CHUNK_SIZE` y `CHUNK_OVERLAP` en `scrum_rag/config.py`.
- Preguntar cosas que esten y no esten en la guia.
- Comparar respuestas con y sin contexto recuperado.
- Revisar si las fuentes citadas realmente contienen la respuesta.
