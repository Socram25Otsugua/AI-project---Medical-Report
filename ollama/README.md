# Custom model (optional)

If you want a model tuned for this project domain, you can create an Ollama model from the `Modelfile`.

## Create

```bash
ollama create radio-medical-ai -f Modelfile
```

## Use in the backend

```bash
export OLLAMA_MODEL=radio-medical-ai
```

