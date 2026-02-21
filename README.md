# University of Manitoba Chatbot

## Prerequisites

- Python 3.8 - 3.10 (Rasa doesn't support Python 3.11+ yet)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup

```bash
ollama pull llama2
export OLLAMA_URL="http://localhost:11434"  # Default URL
```

## Training the Model

```bash
rasa train
```

## Running the Chatbot

You need to run two processes:

### Terminal 1: Start the Action Server

```bash
rasa run actions
```

### Terminal 2: Start the Rasa Server

```bash
rasa shell
```

**For REST API:**

```bash
rasa run --enable-api --cors "*"
```

## Running again after the setup

- Use 2 terminals :
- In the first terminal : change the envirment to run python <= 3.10 as follows
  
  ```bash
  conda activate env_name
  cd 'to the same directory as the project'
  rasa run actions
  ```
- In the second terminal (optional if you want to interact with chat directly from terminal)
  
  ```bash
  conda activate env_name
  cd 'to the same directory as the project'
  rasa train
  rasa shell
  ``` 

