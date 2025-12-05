"""Text cleaning utilities - removes markdown formatting and thinking/reasoning."""
import re
from typing import Optional


def remove_thinking(text: str) -> str:
    """
    Remove model thinking/reasoning patterns from text.
    Removes: <thinking>...</thinking>, <reasoning>...</reasoning>, etc.
    """
    if not text:
        return text
    
    # Remove XML-style thinking tags (most common pattern)
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<reasoning>.*?</reasoning>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<thought>.*?</thought>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<internal>.*?</internal>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove thinking patterns with different formats
    text = re.sub(r'\[thinking\].*?\[/thinking\]', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\[reasoning\].*?\[/reasoning\]', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Split into sentences/paragraphs to identify thinking vs response
    # Look for patterns where thinking ends and actual response begins
    # Common pattern: "Okay, [thinking]. [Actual response starts here]"
    
    # Remove thinking prefixes - detect and remove thinking sentences
    # Pattern: Sentences that describe internal reasoning before actual response
    
    # Split text into sentences (handle periods, exclamation, question marks)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    filtered_sentences = []
    found_response_start = False
    
    # Thinking indicators - phrases that indicate internal reasoning
    thinking_phrases = [
        'i need to respond',
        'i should recall',
        'i must avoid',
        'i should check',
        'the user might be',
        'i should inform',
        'let me make sure',
        'first, i should',
        'the user is asking',
        'i need to',
        'i must',
    ]
    
    # Response starters - phrases that indicate actual response to user
    response_starters = [
        "i'm sorry",
        "i can't",
        "i cannot",
        "i don't",
        "i won't",
        "i'm unable",
        "i'm not able",
        "i apologize",
        "unfortunately",
        "i understand",
        "i appreciate",
        "providing information",
        "i encourage you",
    ]
    
    for sentence in sentences:
        sentence_stripped = sentence.strip()
        if not sentence_stripped:
            continue
            
        sentence_lower = sentence_stripped.lower()
        
        # Check if this sentence starts the actual response
        is_response_start = any(sentence_lower.startswith(starter) for starter in response_starters)
        
        # Check if this sentence contains thinking indicators
        is_thinking = any(phrase in sentence_lower for phrase in thinking_phrases)
        
        # Special case: "Okay," at start usually indicates thinking
        if sentence_stripped.startswith('Okay,') and not found_response_start:
            is_thinking = True
        
        if is_response_start:
            found_response_start = True
            filtered_sentences.append(sentence_stripped)
        elif found_response_start:
            # After response starts, include everything
            filtered_sentences.append(sentence_stripped)
        elif not is_thinking:
            # Include non-thinking sentences before response starts
            # But skip if it starts with "Okay," or "Let me think"
            if not (sentence_stripped.startswith('Okay,') or sentence_stripped.lower().startswith('let me think')):
                filtered_sentences.append(sentence_stripped)
        # Skip thinking sentences before response starts
    
    # If no response starter found, try to find where thinking ends
    if not found_response_start and filtered_sentences:
        # Look for first non-thinking sentence
        final_sentences = []
        for sentence in filtered_sentences:
            sentence_lower = sentence.lower()
            if not any(phrase in sentence_lower for phrase in thinking_phrases):
                final_sentences.append(sentence)
        if final_sentences:
            filtered_sentences = final_sentences
    
    text = ' '.join(filtered_sentences)
    
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    return text


def strip_markdown(text: str) -> str:
    """
    Remove markdown formatting from text.
    Removes: **bold**, *italic*, # headers, - lists, `code`, etc.
    """
    if not text:
        return text
    
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    
    # Remove headers (# ## ###) - handle both with and without space after #
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Remove bold (**text** or __text__) - handle multiple occurrences
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    # Also handle standalone ** or __
    text = text.replace('**', '').replace('__', '')
    
    # Remove italic (*text* or _text_) - be careful not to remove multiplication
    # Only remove if it's clearly markdown (surrounded by word boundaries)
    text = re.sub(r'(?<!\w)\*([^*\n]+)\*(?!\*)', r'\1', text)
    text = re.sub(r'(?<!\w)_([^_\n]+)_(?!_)', r'\1', text)
    # Remove remaining standalone * and _ that might be markdown
    text = re.sub(r'(?<!\*)\*(?!\*)', '', text)  # Remove * that aren't part of **
    text = re.sub(r'(?<!_)_(?!_)', '', text)  # Remove _ that aren't part of __
    
    # Remove strikethrough
    text = re.sub(r'~~([^~]+)~~', r'\1', text)
    
    # Remove list markers (- * +)
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    
    # Remove numbered lists
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
    
    # Remove horizontal rules
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\*\*\s*$', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to one
    text = text.strip()
    
    return text


def clean_response(text: str) -> str:
    """
    Complete response cleaning: removes thinking/reasoning and markdown.
    This is the main function to use for cleaning LLM responses.
    """
    if not text:
        return text
    
    # First remove thinking/reasoning
    text = remove_thinking(text)
    
    # Then remove markdown
    text = strip_markdown(text)
    
    return text

