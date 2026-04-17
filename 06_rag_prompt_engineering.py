"""
Step 6: RAG Prompt Engineering
Context-grounded LLM responses with advanced prompting techniques
Integrates: Retrieval + Few-Shot + ReAct + Insufficient Context Handling
"""

from retrieval_api import EventRetriever
from typing import Dict, List, Optional, Tuple
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Note: Requires: pip install openai
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. Install with: pip install openai")


class RAGPromptEngine:
    """Advanced RAG with prompt engineering and LLM integration"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", 
                 api_key: Optional[str] = None):
        """Initialize RAG engine"""
        self.model = model
        self.retriever = EventRetriever()
        
        # Initialize OpenAI if available
        if OPENAI_AVAILABLE:
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
                logger.info(f"[OK] OpenAI client initialized (model: {model})")
            else:
                self.client = None
                logger.warning("OPENAI_API_KEY not set. LLM queries will be simulated.")
        else:
            self.client = None
        
        # Few-shot examples for in-context learning
        self.few_shot_examples = self._load_few_shot_examples()
    
    def _load_few_shot_examples(self) -> List[Dict]:
        """Load few-shot examples for better LLM responses"""
        return [
            {
                "query": "What happened with the fire emergency at component 100?",
                "context_snippet": "Alarm ID 102: HIGH priority Fire Emergency event. occurred on 2025-05-20 08:09:59, affecting Component 100 (Enterprise System), Primary agency: Police",
                "expected_answer": "A HIGH priority Fire Emergency occurred on 2025-05-20 at 08:09:59 UTC affecting Component 100 (Enterprise System). The Police department was the primary responding agency."
            },
            {
                "query": "Which components are experiencing critical alarms?",
                "context_snippet": "Alarm ID 153: CRITICAL priority Fire Emergency from Component 103. Alarm ID 37764: CRITICAL priority Security Malfunction from Component 315.",
                "expected_answer": "Based on the operational data, Components 103 and 315 are experiencing critical alarms. Component 103 has a critical fire emergency, while Component 315 has a critical security malfunction."
            },
            {
                "query": "How many water leakage events occurred in September?",
                "context_snippet": "Alarm ID 38037: HIGH priority Water Leakage (September, Component 313), Alarm ID 38096: HIGH priority Water Leakage (September, Component 312)",
                "expected_answer": "At least 2 water leakage events occurred in September 2025: one from Component 313 and one from Component 312, both marked as HIGH priority."
            }
        ]
    
    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for context-grounded responses"""
        return """You are an expert Event Intelligence analyst helping to answer questions about operational incidents and alarms.

CRITICAL RULES:
1. ANSWER STRICTLY FROM THE PROVIDED CONTEXT - Do not use external knowledge
2. If information is not in the context, clearly state "This information is not available in the provided context"
3. Be precise, factual, and concise
4. Cite specific alarm IDs, components, and timestamps when available
5. Acknowledge uncertainty when pattern is unclear from limited data

RESPONSE FORMAT:
- Start with a direct answer
- Support with specific evidence from context
- Include relevant metadata (alarm IDs, priorities, components)
- Note limitations if data is insufficient

CONTEXT-SPECIFIC METADATA:
- Priority levels: Critical, High, Low
- Components: Numbered identifiers (103, 312, 313, etc.)
- Alarms: Include alarm ID, type, timestamp, component
- Temporal: Use exact dates and times from data
- Agencies: Police, Civil Defence, EMS, etc."""
    
    def _build_few_shot_prompt(self) -> str:
        """Build few-shot learning examples"""
        few_shot = "\n\n=== EXAMPLES ===\n"
        
        for i, example in enumerate(self.few_shot_examples, 1):
            few_shot += f"\nExample {i}:\n"
            few_shot += f"User Query: {example['query']}\n"
            few_shot += f"Available Context: {example['context_snippet']}\n"
            few_shot += f"Assistant Response: {example['expected_answer']}\n"
            few_shot += "-" * 70
        
        return few_shot
    
    def _build_react_prompt(self, query: str, context: str, 
                           reasoning_steps: List[str]) -> str:
        """Build ReAct (Reasoning + Acting) prompt"""
        react_prompt = f"""Use the following structured approach to answer the question:

THINK: Analyze what the question is asking and what information is needed
ACT: Search for and extract relevant information from the context
ANSWER: Provide a clear, fact-based response

QUESTION: {query}

CONTEXT PROVIDED:
{context}

Now, let's think through this step by step:
1. THINK: What specific information does this question require?
2. ACT: What did we find in the context that addresses this?
3. ANSWER: Based on our analysis, what is the answer?

Provide your response in this format:
[THOUGHT] ... 
[ACTION] ...
[OBSERVATION] ...
[ANSWER] ..."""
        return react_prompt
    
    def retrieve_context(self, query: str, k: int = 5,
                        priority_filter: Optional[str] = None,
                        component_filter: Optional[int] = None) -> Tuple[List[Dict], bool]:
        """
        Retrieve relevant context for a query
        
        Returns:
            Tuple of (retrieved_chunks, has_sufficient_context)
        """
        try:
            results = self.retriever.retrieve(
                query,
                k=k,
                priority_filter=priority_filter,
                component_filter=component_filter
            )
            
            # Determine if context is sufficient
            # Threshold: at least 2 results with reasonable similarity
            has_sufficient = len(results) >= 2 and results[0]['similarity'] > 0.15
            
            return results, has_sufficient
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return [], False
    
    def format_context_for_llm(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks as context for LLM"""
        if not chunks:
            return "No relevant context retrieved."
        
        context = "=== EVENT CONTEXT (From Operational Database) ===\n\n"
        
        for i, chunk in enumerate(chunks, 1):
            context += f"[Context {i}]\n"
            context += f"Alarm ID: {chunk['alarm_id']}\n"
            context += f"Priority: {chunk['priority']}\n"
            
            if chunk.get('component_id'):
                context += f"Component: {chunk['component_id']}\n"
            if chunk.get('month'):
                context += f"Month: {chunk['month']}\n"
            if chunk.get('alarm_name'):
                context += f"Event Type: {chunk['alarm_name']}\n"
            if chunk.get('similarity'):
                context += f"Relevance Score: {chunk['similarity']:.2%}\n"
            
            context += f"Details: {chunk['text']}\n\n"
        
        return context
    
    def handle_insufficient_context(self, query: str, 
                                   available_results: int) -> str:
        """Generate helpful response when context is insufficient"""
        if available_results == 0:
            return (
                f"Unable to find relevant event data for your query: '{query}'\n\n"
                "Suggestions:\n"
                "1. Try a broader search term (e.g., 'alarm' instead of specific event name)\n"
                "2. Search by component ID or priority level\n"
                "3. Search by time period (e.g., 'September events')\n"
                "\nNote: The system has access to events from May through November 2025."
            )
        else:
            return (
                f"Limited context available for query: '{query}'\n"
                f"Found {available_results} event(s) but confidence is low.\n\n"
                "The available data may not be sufficient to answer this question accurately.\n"
                "Consider searching with more specific filters like:\n"
                "- Priority level (Critical, High, Low)\n"
                "- Component ID\n"
                "- Time period\n"
                "- Event type"
            )
    
    def query_with_llm(self, query: str, use_react: bool = False,
                      use_few_shot: bool = True,
                      max_context_chunks: int = 5) -> Dict:
        """
        Complete RAG query with LLM
        
        Args:
            query: User query
            use_react: Use ReAct prompting technique
            use_few_shot: Include few-shot examples
            max_context_chunks: Maximum context chunks to retrieve
            
        Returns:
            Dict with query, context, reasoning, and answer
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"RAG Query: {query}")
        logger.info(f"{'='*70}")
        
        # Retrieve context
        context_chunks, has_sufficient = self.retrieve_context(
            query, 
            k=max_context_chunks
        )
        
        logger.info(f"Retrieved {len(context_chunks)} context chunks"
                   f" (sufficient: {has_sufficient})")
        
        # Handle insufficient context
        if not has_sufficient:
            answer = self.handle_insufficient_context(query, len(context_chunks))
            return {
                'query': query,
                'context_chunks': context_chunks,
                'context_text': self.format_context_for_llm(context_chunks),
                'has_sufficient_context': False,
                'reasoning': "Insufficient context available",
                'answer': answer,
                'method': 'insufficient_context_handler'
            }
        
        # Format context
        context_text = self.format_context_for_llm(context_chunks)
        
        # Build prompt
        if use_react:
            user_message = self._build_react_prompt(query, context_text, [])
            method = "ReAct"
        else:
            user_message = f"Based on the provided event context, answer this question: {query}\n\n{context_text}"
            method = "Standard"
        
        # Build messages
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
        ]
        
        # Add few-shot examples if enabled
        if use_few_shot:
            few_shot_text = self._build_few_shot_prompt()
            messages.append({
                "role": "system",
                "content": f"Learn from these examples:\n{few_shot_text}"
            })
        
        messages.append({"role": "user", "content": user_message})
        
        # Query LLM
        if self.client:
            logger.info(f"Querying LLM with {method} prompting...")
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,  # Low temperature for factual responses
                    max_tokens=500
                )
                answer = response.choices[0].message.content
                logger.info("[OK] LLM response received")
            except Exception as e:
                logger.error(f"LLM query failed: {e}")
                answer = f"Error querying LLM: {str(e)}"
        else:
            # Simulated response when OpenAI not available
            logger.info("Simulating LLM response (OpenAI not configured)")
            answer = self._simulate_llm_response(query, context_chunks)
        
        return {
            'query': query,
            'context_chunks': context_chunks,
            'context_text': context_text,
            'has_sufficient_context': True,
            'reasoning': f"Retrieved {len(context_chunks)} relevant events",
            'answer': answer,
            'method': method,
            'few_shot_used': use_few_shot,
            'react_used': use_react
        }
    
    def _simulate_llm_response(self, query: str, 
                              chunks: List[Dict]) -> str:
        """Simulate LLM response when OpenAI not available"""
        if not chunks:
            return "No relevant event data found for this query."
        
        # Extract key information from chunks
        alarms = [c['alarm_id'] for c in chunks]
        priorities = set(c['priority'] for c in chunks)
        components = set(c['component_id'] for c in chunks if c['component_id'])
        
        response = f"Based on the operational data:\n\n"
        
        if "how many" in query.lower() or "count" in query.lower():
            response += f"Found {len(chunks)} relevant event(s) with IDs: {', '.join(map(str, alarms))}\n"
        
        if priorities:
            response += f"Priority levels involved: {', '.join(sorted(priorities))}\n"
        
        if components:
            response += f"Affected components: {', '.join(map(str, sorted(components)))}\n"
        
        response += f"\nDetails from top result:\n{chunks[0]['text']}"
        
        return response
    
    def interactive_session(self):
        """Start interactive RAG session"""
        logger.info("\n" + "="*70)
        logger.info("Event Intelligence RAG System - Interactive Session")
        logger.info("="*70)
        logger.info("Type 'quit' to exit, 'help' for commands\n")
        
        while True:
            try:
                user_query = input("\n📌 Your question: ").strip()
                
                if user_query.lower() == 'quit':
                    logger.info("Exiting...")
                    break
                
                if user_query.lower() == 'help':
                    logger.info("""
Commands:
  - Regular query: Type any question about events
  - 'critical' keyword: Auto-filter to critical priority
  - 'component XXX': Auto-filter by component ID
  - 'react': Use ReAct prompting
  - 'quit': Exit session
                    """)
                    continue
                
                if not user_query:
                    continue
                
                # Check for special commands
                use_react = False
                priority_filter = None
                component_filter = None
                
                if 'critical' in user_query.lower():
                    priority_filter = 'Critical'
                    user_query = user_query.replace('critical', '').strip()
                
                if 'react' in user_query.lower():
                    use_react = True
                    user_query = user_query.replace('react', '').strip()
                
                # Extract component filter if present
                import re
                comp_match = re.search(r'component\s+(\d+)', user_query, re.IGNORECASE)
                if comp_match:
                    component_filter = int(comp_match.group(1))
                    user_query = re.sub(r'component\s+\d+', '', user_query, 
                                       flags=re.IGNORECASE).strip()
                
                # Run RAG query
                result = self.query_with_llm(
                    user_query,
                    use_react=use_react,
                    use_few_shot=True
                )
                
                # Display results
                logger.info(f"\n{'─'*70}")
                logger.info(f"Answer:")
                logger.info(result['answer'])
                logger.info(f"\n[Method: {result['method']}]")
                logger.info(f"[Context Quality: {'Sufficient' if result['has_sufficient_context'] else 'Limited'}]")
                
            except KeyboardInterrupt:
                logger.info("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
    
    def close(self):
        """Clean up resources"""
        self.retriever.close()


def main():
    """Demonstrate RAG prompt engineering"""
    # Initialize RAG engine
    rag = RAGPromptEngine()
    
    logger.info("\n" + "="*70)
    logger.info("STEP 6: RAG PROMPT ENGINEERING DEMONSTRATION")
    logger.info("="*70)
    
    # Test queries
    test_queries = [
        ("What critical alarms occurred from component 103?", {'use_react': False}),
        ("Why are there so many high priority water leakage events in component 313?", 
         {'use_react': True}),
        ("Which components experienced security malfunction alerts?", {'use_react': False}),
        ("How many fire emergency events were recorded in May?", {'use_react': True}),
    ]
    
    for query, options in test_queries:
        result = rag.query_with_llm(query, **options)
        
        logger.info(f"\n{'─'*70}")
        logger.info(f"Query: {query}")
        logger.info(f"Context Chunks: {len(result['context_chunks'])}")
        logger.info(f"Sufficient Context: {result['has_sufficient_context']}")
        logger.info(f"\nAnswer:\n{result['answer']}")
        logger.info(f"\nMethod: {result['method']} | Few-Shot: {result.get('few_shot_used')} | ReAct: {result.get('react_used')}")
    
    # Interactive session
    logger.info("\n" + "="*70)
    response = input("\nStart interactive session? (y/n): ").strip().lower()
    if response == 'y':
        rag.interactive_session()
    
    rag.close()
    
    logger.info("\n" + "="*70)
    logger.info("[OK] Step 6 Complete: RAG Prompt Engineering successful!")
    logger.info("="*70 + "\n")
    
    return True


if __name__ == '__main__':
    main()
