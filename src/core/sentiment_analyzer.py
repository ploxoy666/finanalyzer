import os
from typing import Dict, List, Optional
from loguru import logger

try:
    from huggingface_hub import InferenceClient
except ImportError:
    InferenceClient = None

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class SentimentAnalyzer:
    """
    Analyzes financial text sentiment using FinBERT via Hugging Face API or Local Fallback.
    """
    
    MODEL_NAME = "ProsusAI/finbert"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.use_api = bool(api_key and InferenceClient)
        self.tokenizer = None
        self.model = None
        
        if self.use_api:
            logger.info("Initialized SentimentAnalyzer with Hugging Face API.")
            self.client = InferenceClient(provider="hf-inference", api_key=api_key)
        else:
            logger.info("Initialized SentimentAnalyzer in Local Mode (transformers).")
            if not TRANSFORMERS_AVAILABLE:
                logger.warning("Transformers not installed. Local mode unavailable.")

    def _load_local_model(self):
        """Lazy load local model to save RAM if API fails or is not used."""
        # Safety check: Don't load 1.2GB model on low-RAM environments (like Streamlit Cloud)
        # unless explicitly permitted.
        is_streamlit_cloud = os.environ.get("STREAMLIT_RUNTIME_ENV") == "cloud" or os.environ.get("HOSTNAME", "").startswith("streamlit")
        
        if is_streamlit_cloud and not self.api_key:
            logger.warning("Running on Streamlit Cloud without API key. Skipping local FinBERT to prevent crash.")
            return

        if not self.model and TRANSFORMERS_AVAILABLE:
            try:
                logger.info("Loading local FinBERT model...")
                self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME, use_safetensors=True)
                self.model.eval()
            except Exception as e:
                logger.error(f"Failed to load local model: {e}")
                self.model = None

    def analyze(self, text: str) -> Dict:
        """
        Analyze text sentiment.
        """
        if not text:
            return {"dominant_sentiment": "neutral", "composite_score": 0.0}
            
        # Truncate text generally for API limits (usually ~XXX tokens)
        # We take first 1500 chars which is roughly 300-400 tokens
        truncated_text = text[:1500] 

        if self.use_api:
            try:
                return self._analyze_api(truncated_text)
            except Exception as e:
                logger.error(f"API Analysis failed: {e}. Falling back to local.")
                # Fallback to local
                self._load_local_model()
                return self._analyze_local(truncated_text)
        else:
            self._load_local_model()
            return self._analyze_local(truncated_text)

    def _analyze_api(self, text: str) -> Dict:
        """Use Hugging Face Inference API."""
        # Returns list of dicts: [{'label': 'neutral', 'score': 0.8}, ...]
        # Or sometimes just one top label depending on params, but text_classification usually returns list.
        # Actually client.text_classification returns a list of classification objects.
        
        results = self.client.text_classification(text, model=self.MODEL_NAME)
        # Result example: [{'label': 'neutral', 'score': 0.90}, {'label': 'positive', 'score': 0.05}...]
        # Actually looking at doc, it might return just list of class scores.
        
        # Let's map results. Assuming standard HF output structure for text-classification task
        # Usually it returns a list of dicts sorted by score.
        
        # Convert classification objects to dict
        scores_dict = {item.label: item.score for item in results}
        
        return self._format_result(scores_dict)

    def _analyze_local(self, text: str) -> Dict:
        """Use local transformers model."""
        if not self.model:
            raise RuntimeError("Local model not loaded and transformers lib missing.")
            
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        scores = predictions[0].tolist()
        labels = ["positive", "negative", "neutral"] # FinBERT standard config
        
        # Verify labels from config if possible, but ProsusAI/finbert is standard.
        scores_dict = {label: score for label, score in zip(labels, scores)}
        
        return self._format_result(scores_dict)

    def _format_result(self, scores_dict: Dict[str, float]) -> Dict:
        """Standardize output format."""
        
        # Ensure all keys exist
        for k in ['positive', 'negative', 'neutral']:
            if k not in scores_dict:
                scores_dict[k] = 0.0
                
        dominant = max(scores_dict, key=scores_dict.get)
        
        # Composite score: (-1 to 1)
        composite = scores_dict['positive'] - scores_dict['negative']
        
        return {
            "dominant_sentiment": dominant,
            "composite_score": composite,
            "breakdown": scores_dict
        }

    def analyze_report(self, pages_text: List[str], max_pages: int = 5) -> Dict:
        """Analyze beginning of report."""
        # Join first few pages
        text = " ".join(pages_text[:max_pages])
        return self.analyze(text)
