# scrum-guide-rag

Leer en ingles: [README.md](README.md)

Un proyecto educativo para construir tu primer RAG local usando la Guia de Scrum 2020.

Este repositorio esta pensado para personas que quieren entender, con un ejemplo pequeno y practico, como funciona un sistema de Retrieval-Augmented Generation: cargar documentos, partirlos en fragmentos, crear embeddings, guardar un indice vectorial, recuperar contexto relevante y conversar con un modelo local.

![Chat web de Scrum Guide RAG](docs/assets/scrum-guide-rag-web-chat.png)

## Que Vas A Construir

Este proyecto implementa un RAG local sobre la Guia de Scrum:

```text
PDF -> chunks -> embeddings -> Chroma -> pregunta -> retrieval -> LLM -> respuesta
```

Incluye:

- ingesta de documentos PDF, TXT y Markdown;
- chunking con LangChain;
- embeddings locales con Ollama;
- base vectorial local con Chroma;
- chat por terminal;
- interfaz web tipo chat;
- modo debug para ver fragmentos recuperados;
- golden dataset para evaluar el RAG;
- metricas basicas de retrieval, abstencion y cobertura de respuesta.

## Por Que Este Proyecto

La Guia de Scrum es un buen primer caso para aprender RAG porque:

- es un documento pequeno;
- tiene conceptos bien definidos;
- permite hacer preguntas con respuesta clara;
- tambien permite hacer preguntas trampa o fuera del documento;
- es facil verificar si el modelo esta inventando.

El objetivo no es solo "chatear con un PDF". La idea es aprender el ciclo completo de un RAG y tener una base que puedas reutilizar para tus propios documentos.

## Stack

- Python
- LangChain
- Chroma
- Ollama
- `nomic-embed-text` para embeddings
- `llama3.2` para generacion
- HTML, CSS y JavaScript vanilla para el frontend

## Estructura Del Proyecto

```text
scrum-guide-rag/
  data/                         # Documento fuente
  eval/
    golden_dataset.jsonl         # Preguntas de prueba
    reports/                     # Reportes generados localmente
  scrum_rag/
    config.py                    # Configuracion principal
    loaders.py                   # Carga de documentos
    ingest.py                    # Indexado
    rag.py                       # Motor RAG
    chat.py                      # Chat por terminal
    search.py                    # Diagnostico de retrieval
    evaluate.py                  # Evaluacion del RAG
    web/
      app.py                     # Servidor web ASGI
      static/                    # Frontend
  requirements.txt
  README.md
  README.es.md
```

## Requisitos

Necesitas Python 3.9+, Ollama y Git.

Instala Ollama desde:

https://ollama.com/download

Descarga los modelos:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

## Instalacion

```bash
git clone https://github.com/lcdosguzman/scrum-guide-rag.git
cd scrum-guide-rag
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

### 1. Indexar La Guia

```bash
python3 -m scrum_rag.ingest
```

Este comando lee los documentos en `data/`, divide el texto en chunks, genera embeddings con `nomic-embed-text` y guarda el indice en `chroma_db/`.

El indexado borra y reconstruye `chroma_db/` para evitar mezclar fragmentos viejos.

### 2. Abrir El Chat Web

```bash
python3 -m uvicorn scrum_rag.web.app:app --host 127.0.0.1 --port 8000
```

Luego abre:

```text
http://127.0.0.1:8000
```

La interfaz web incluye modo estandar, modo debug, boton para limpiar el chat y enlace a la guia original.

### 3. Chat Por Terminal

```bash
python3 -m scrum_rag.chat
```

Comandos disponibles:

- `/sources`: muestra las fuentes de la ultima respuesta.
- `/exit`: salir.

### 4. Diagnosticar Retrieval

Antes de culpar al modelo, revisa que fragmentos recupera el RAG:

```bash
python3 -m scrum_rag.search "oopsla"
```

Esto ayuda a saber si un fallo viene del retrieval o de la generacion.

### 5. Evaluar El RAG

Evaluar solo retrieval:

```bash
python3 -m scrum_rag.evaluate --retrieval-only
```

Evaluar el pipeline completo:

```bash
python3 -m scrum_rag.evaluate
```

Los reportes se guardan en `eval/reports/`.

El golden dataset esta en `eval/golden_dataset.jsonl`.

## Que Mide La Evaluacion

El proyecto incluye una evaluacion simple y local:

- `hit_rate`: si encontro evidencia esperada.
- `precision_at_k`: proporcion de fragmentos recuperados que eran relevantes.
- `mrr`: que tan arriba aparece la primera evidencia correcta.
- `answer_term_coverage`: cobertura de terminos esperados en respuestas.
- `abstention_accuracy`: si el RAG se abstiene cuando la guia no contiene la respuesta.
- latencia promedio y p95.

Esto convierte al RAG en algo medible, no solo en algo que "parece responder bien".

## Ideas Para Aprender

Prueba cambiar:

- `CHUNK_SIZE`
- `CHUNK_OVERLAP`
- `RETRIEVAL_K`
- el prompt en `scrum_rag/rag.py`
- el modelo de generacion en Ollama
- el modelo de embeddings

Despues de cada cambio, ejecuta:

```bash
python3 -m scrum_rag.evaluate --retrieval-only
python3 -m scrum_rag.evaluate
```

Asi puedes ver si tu cambio mejoro o empeoro el sistema.

## Limitaciones

Este proyecto es intencionalmente simple:

- no usa autenticacion;
- no tiene base de datos de usuarios;
- no implementa ingesta incremental;
- no usa reranking avanzado;
- no usa RAGAS ni DeepEval todavia;
- no esta pensado como producto listo para produccion.

Es un punto de partida para aprender y experimentar.

## Proximos Pasos

Algunas mejoras posibles:

- agregar mas documentos;
- hacer ingesta incremental;
- agregar reranking;
- probar otros modelos locales;
- integrar RAGAS o DeepEval;
- guardar logs de preguntas reales;
- convertir preguntas fallidas en nuevos casos del golden dataset;
- migrar el frontend a React si el proyecto crece.
