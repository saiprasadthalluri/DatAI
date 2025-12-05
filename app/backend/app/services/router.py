"""Router logic: Best Model passthrough or Mixture-of-Endpoints."""
import os
import random
import logging
from typing import Dict, Any
from ..core.config import settings

logger = logging.getLogger(__name__)


def _intent_classification(message: str) -> str:
    """
    Classify query into specialist model: theory-specialist, code-specialist, or math-specialist.
    
    Args:
        message: User message
        
    Returns:
        Model friendly name: "theory-specialist", "code-specialist", or "math-specialist"
    """
    import re
    
    msg_lower = message.lower()
    
    # Code-related keywords
    CODE_KEYWORDS = [
        "code", "coding", "program", "programming", "function", "class",
        "debug", "error", "bug", "script", "python", "javascript", "java",
        "sql", "api", "implement", "algorithm", "data structure", "syntax",
        "compile", "runtime", "exception", "variable", "loop", "array",
        "write a", "create a function", "fix this", "refactor", "show me code",
        "example code", "code snippet", "how to code", "write code",
        "programming language", "library", "package", "module", "import",
        "dictionary", "list comprehension", "lambda", "decorator"
    ]
    
    # Math-related keywords
    MATH_KEYWORDS = [
        "calculate", "compute", "solve", "equation", "formula", "math",
        "derivative", "integral", "probability", "statistics", "matrix",
        "vector", "linear algebra", "calculus", "proof", "theorem",
        "sum", "product", "factorial", "logarithm", "exponential",
        "regression", "correlation", "variance", "standard deviation",
        "hypothesis", "p-value", "confidence interval", "mean", "median",
        "mode", "distribution", "normal distribution", "t-test", "chi-square",
        "anova", "bayesian", "optimization", "minimize", "maximize"
    ]
    
    # Theory-related keywords
    THEORY_KEYWORDS = [
        "explain", "what is", "how does", "describe", "concept",
        "theory", "principle", "why", "definition", "overview",
        "introduction", "understand", "intuition", "behind",
        "machine learning", "deep learning", "neural network",
        "pca", "clustering", "classification", "supervised",
        "unsupervised", "reinforcement learning", "gradient descent",
        "backpropagation", "overfitting", "regularization", "bias",
        "feature engineering", "cross-validation", "ensemble",
        "data science", "data analysis", "exploratory", "eda",
        "model", "training", "testing", "validation", "accuracy",
        "precision", "recall", "f1-score", "roc", "auc", "confusion matrix"
    ]
    
    # Count keyword matches
    code_score = sum(1 for kw in CODE_KEYWORDS if kw in msg_lower)
    math_score = sum(1 for kw in MATH_KEYWORDS if kw in msg_lower)
    theory_score = sum(1 for kw in THEORY_KEYWORDS if kw in msg_lower)
    
    # Check for code blocks or programming patterns (strong signal)
    code_patterns = [
        r'def\s+\w+\s*\(', r'class\s+\w+', r'import\s+\w+', r'from\s+\w+\s+import',
        r'function\s+\w+', r'const\s+\w+', r'let\s+\w+', r'var\s+\w+',
        r'print\s*\(', r'return\s+', r'if\s+.*:', r'for\s+.*in', r'while\s+',
        r'\.py\b', r'\.js\b', r'\.java\b', r'```', r'<code>'
    ]
    if any(re.search(pattern, message, re.IGNORECASE) for pattern in code_patterns):
        code_score += 5  # Strong signal for code
    
    # Check for math expressions (strong signal)
    math_patterns = [
        r'[0-9]+\s*[\+\-\*\/\=\^]\s*[0-9]+', r'∑|∫|√|²|³|π|∞',
        r'[a-z]\s*=\s*[0-9]', r'f\(x\)', r'lim\s*\(', r'log\s*\(',
        r'[0-9]+\s*%', r'[0-9]+\s*/\s*[0-9]+', r'\$\s*[0-9]'
    ]
    if any(re.search(pattern, message, re.IGNORECASE) for pattern in math_patterns):
        math_score += 5  # Strong signal for math
    
    # Check for theory/explanation patterns
    theory_patterns = [
        r'^what\s+is', r'^how\s+does', r'^why\s+', r'^explain\s+',
        r'^describe\s+', r'^tell\s+me\s+about', r'^can\s+you\s+explain'
    ]
    if any(re.search(pattern, message, re.IGNORECASE) for pattern in theory_patterns):
        theory_score += 2  # Boost for explanation requests
    
    # Determine winner
    scores = {
        "code-specialist": code_score,
        "math-specialist": math_score,
        "theory-specialist": theory_score,
    }
    
    max_score = max(scores.values())
    
    # Default to theory if no clear winner or all zeros
    if max_score == 0:
        return "theory-specialist"
    
    # Return highest scoring category
    for model, score in scores.items():
        if score == max_score:
            return model
    
    return "theory-specialist"


class QueryRouter:
    """
    Classifies user queries to route to the appropriate specialist model.
    """
    
    def classify(self, query: str) -> str:
        """
        Classify a query into: theory-specialist, code-specialist, or math-specialist.
        """
        return _intent_classification(query)


# Singleton
_router = None


def get_query_router() -> QueryRouter:
    """Get or create query router instance."""
    global _router
    if _router is None:
        _router = QueryRouter()
    return _router


async def decide(meta: Dict[str, Any], message: str) -> Dict[str, Any]:
    """
    Decide which specialist model to use based on query content.
    
    Args:
        meta: Chat metadata (model, temperature, etc.)
        message: User message
        
    Returns:
        Dictionary with:
        - model: Friendly model name ("theory-specialist", "code-specialist", "math-specialist", or "auto")
        - confidence: Confidence score (0.0-1.0)
        - reasons: dict - Decision reasoning
    """
    # Check if model is explicitly specified
    explicit_model = meta.get("model")
    if explicit_model and explicit_model in ["theory-specialist", "code-specialist", "math-specialist"]:
        return {
            "model": explicit_model,
            "confidence": 1.0,
            "reasons": {
                "model": explicit_model,
                "source": "explicit_user_selection"
            }
        }
    
    # Auto-route based on query content
    if explicit_model == "auto" or not explicit_model:
        selected_model = _intent_classification(message)
        
        # Calculate confidence based on keyword matches
        confidence = 0.75 if selected_model != "theory-specialist" else 0.65
        
        return {
            "model": selected_model,
            "confidence": confidence,
            "reasons": {
                "model": selected_model,
                "source": "auto_routing"
            }
        }
    
    # Default fallback
    return {
        "model": "theory-specialist",
        "confidence": 0.5,
        "reasons": {
            "model": "theory-specialist",
            "source": "default_fallback"
        }
    }




