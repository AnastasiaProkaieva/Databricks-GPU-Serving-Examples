# Databricks notebook source
import pandas as pd
import numpy as np
import transformers
import mlflow
import torch

# COMMAND ----------

from huggingface_hub import snapshot_download
# Download the model snapshot from huggingface
snapshot_location = snapshot_download(repo_id="textattack/bert-base-uncased-imdb")

# COMMAND ----------

class BertSentimentClassifier(mlflow.pyfunc.PythonModel):
  def load_context(self, context):
    # Initialize tokenizer and language model
    self.tokenizer = transformers.AutoTokenizer.from_pretrained(
      context.artifacts['repository'])
    self.model = transformers.AutoModelForSequenceClassification.from_pretrained(
      context.artifacts['repository']).to('cuda')

  def predict(self, context, model_input):
    message = model_input["review"][0]
    
    # Encode input and generate prediction
    encoded_input = self.tokenizer.encode(message, return_tensors='pt', max_length=512, truncation=True).to('cuda')
    
    # Generate sentiment prediction
    with torch.no_grad():
      output = self.model(encoded_input)[0]
      _, prediction = torch.max(output, dim=1)
    
    return "Positive" if prediction == 1 else "Negative"

# COMMAND ----------

# Log the model with its details such as artifacts, pip requirements and input example
with mlflow.start_run() as run:  
    mlflow.pyfunc.log_model(
        "model",
        python_model=BertSentimentClassifier(),
        artifacts={'repository' : snapshot_location},
        pip_requirements=["torch", "transformers"],
        input_example=pd.DataFrame({"review":["I love this movie."]}),
    )

# COMMAND ----------

# Load the logged model
loaded_model = mlflow.pyfunc.load_model("runs:/"+run.info.run_id+"/model")

# COMMAND ----------

# Make a prediction using the loaded model
input_example=pd.DataFrame({"review":["I love this movie."]})
print(loaded_model.predict(input_example))
