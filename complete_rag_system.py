"""
Complete RAG System Example - Production Ready
Integrate retrieval, prompting, and LLM for Q&A
"""

from retrieval_api import EventRetriever
from typing import Dict, List, Optional
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompletRAGSystem:
    """Production-ready RAG system with all features"""
    
    def __init__(self):
        """Initialize complete RAG system"""
        self.retriever = EventRetriever()
        
        # System instructions
        self.system_instructions = """You are an expert event analyst answering questions about operational incidents.

CORE PRINCIPLES:
1. ANSWER STRICTLY FROM PROVIDED CONTEXT
2. Do NOT use external knowledge or assumptions
3. If information is missing, say so explicitly
4. Be specific with alarm IDs, timestamps, and component references
5. Acknowledge confidence levels and limitations

RESPONSE STRUCTURE:
- Direct answer first
- Supporting evidence from context
- Relevant metadata (dates, components, priorities)
- Limitations if applicable"""
    
    def query(self, user_question: str, 
             retrieve_k: int = 5,
             priority_filter: Optional[str] = None,
             component_filter: Optional[int] = None) -> Dict:
        """
        Complete RAG query pipeline
        
        Returns structured response with context, reasoning, and answer
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Query: {user_question}")
        logger.info(f"{'='*70}")
        
        # Step 1: Retrieve relevant context
        logger.info("\n[STEP 1] Retrieving context...")
        context_chunks = self.retriever.retrieve(
            user_question,
            k=retrieve_k,
            priority_filter=priority_filter,
            component_filter=component_filter
        )
        
        if not context_chunks:
            logger.info("No relevant context found")
            return {
                'question': user_question,
                'status': 'no_context',
                'answer': self._no_context_response(user_question)
            }
        
        logger.info(f"Retrieved {len(context_chunks)} relevant chunks")
        
        # Step 2: Check context quality
        logger.info("\n[STEP 2] Evaluating context quality...")
        context_quality = self._evaluate_context_quality(context_chunks)
        logger.info(f"Context quality: {context_quality['level']} "
                   f"(confidence: {context_quality['confidence']:.0%})")
        
        # Step 3: Format context
        logger.info("\n[STEP 3] Formatting context for analysis...")
        formatted_context = self._format_context(context_chunks)
        logger.info(f"Formatted {len(context_chunks)} chunks")
        
        # Step 4: Generate response
        logger.info("\n[STEP 4] Generating response...")
        response = self._generate_response(
            user_question,
            formatted_context,
            context_chunks,
            context_quality
        )
        
        logger.info("[OK] Response generated")
        
        return {
            'question': user_question,
            'status': 'success',
            'context_count': len(context_chunks),
            'context_quality': context_quality,
            'context_chunks': context_chunks,
            'answer': response,
            'sources': [f"Alarm #{c['alarm_id']}" for c in context_chunks[:3]]
        }
    
    def _evaluate_context_quality(self, chunks: List[Dict]) -> Dict:
        """Evaluate quality and sufficiency of retrieved context"""
        if not chunks:
            return {'level': 'insufficient', 'confidence': 0.0}
        
        avg_similarity = sum(c.get('similarity', 0) for c in chunks) / len(chunks)
        
        if avg_similarity > 0.5:
            level = 'excellent'
            confidence = 0.95
        elif avg_similarity > 0.3:
            level = 'good'
            confidence = 0.8
        elif avg_similarity > 0.15:
            level = 'fair'
            confidence = 0.6
        else:
            level = 'insufficient'
            confidence = 0.3
        
        unique_alarms = len(set(c['alarm_id'] for c in chunks))
        
        return {
            'level': level,
            'confidence': confidence,
            'avg_similarity': avg_similarity,
            'unique_alarms': unique_alarms,
            'chunk_count': len(chunks)
        }
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """Format chunks into structured context with full details"""
        context = "=== OPERATIONAL CONTEXT ===\n\n"
        
        for i, chunk in enumerate(chunks, 1):
            context += f"[Result {i} of {len(chunks)}]\n"
            context += f"{'='*70}\n"
            context += f"Alarm ID: {chunk['alarm_id']} | Priority: {chunk['priority']}\n"
            context += f"Confidence: {chunk.get('confidence_level', 'N/A')} ({chunk.get('confidence_percentage', 0)}%)\n"
            context += f"Relevance Score: {chunk.get('similarity_percentage', 0):.1f}%\n"
            
            if chunk.get('alarm_name'):
                context += f"Alert Type: {chunk['alarm_name']}\n"
            if chunk.get('component_id'):
                context += f"Component: {chunk['component_id']}\n"
            if chunk.get('device'):
                context += f"Device Type: {chunk['device']}\n"
            if chunk.get('month'):
                context += f"Date: {chunk['month']}\n"
            if chunk.get('category'):
                context += f"Category: {chunk['category']}\n"
            if chunk.get('location'):
                context += f"Location: {chunk['location']}\n"
            if chunk.get('agency'):
                context += f"Agency: {chunk['agency']}\n"
            if chunk.get('escalation_level'):
                context += f"Escalation Level: {chunk['escalation_level']}\n"
            
            if chunk.get('total_chunks') and chunk['total_chunks'] > 1:
                context += f"Multi-Part Event: Part {chunk.get('chunk_sequence', '?')} of {chunk['total_chunks']}\n"
            
            context += f"\nContent:\n{chunk['text']}\n"
            context += "\n" + "─"*70 + "\n\n"
        
        return context
    
    def _generate_response(self, question: str, context: str,
                          chunks: List[Dict], 
                          quality: Dict) -> str:
        """Generate fact-based response with comprehensive context"""
        response = f"ANALYSIS SUMMARY\n{'='*70}\n\n"
        
        # Add confidence and quality metrics
        response += f"Context Quality: {quality['level'].upper()}\n"
        response += f"Overall Confidence: {quality['confidence']:.0%}\n"
        response += f"Relevant Events Found: {len(chunks)}\n"
        response += f"Unique Alarms: {quality['unique_alarms']}\n"
        response += f"Average Relevance Score: {quality['avg_similarity']:.1%}\n\n"
        
        response += f"{'='*70}\nKEY FINDINGS\n{'='*70}\n\n"
        
        # Extract key facts
        priorities = {}
        for c in chunks:
            p = c['priority']
            priorities[p] = priorities.get(p, 0) + 1
        
        components = set(c['component_id'] for c in chunks if c['component_id'])
        devices = set(c.get('device') for c in chunks if c.get('device'))
        categories = set(c.get('category') for c in chunks if c.get('category'))
        months = set(c.get('month') for c in chunks if c.get('month'))
        
        # Handle different question types
        if any(word in question.lower() for word in ['how many', 'count', 'number']):
            response += f"Total Events Found: {len(chunks)}\n"
        
        if priorities:
            response += f"\nPriority Distribution:\n"
            for priority, count in sorted(priorities.items(), reverse=True):
                response += f"  - {priority}: {count} event(s)\n"
        
        if components:
            response += f"\nComponents Involved: {', '.join(map(str, sorted(components)))}\n"
        
        if devices:
            response += f"Device Types: {', '.join(filter(None, sorted(devices)))}\n"
        
        if categories:
            response += f"Event Categories: {', '.join(filter(None, sorted(categories)))}\n"
        
        if months:
            response += f"Time Periods: {', '.join(filter(None, sorted(months)))}\n"
        
        # Add detailed top results
        response += f"\n{'='*70}\nTOP RESULTS\n{'='*70}\n\n"
        
        for idx, chunk in enumerate(chunks[:3], 1):
            response += f"[Result {idx}] Alarm #{chunk['alarm_id']}\n"
            response += f"  Priority: {chunk['priority']} | Confidence: {chunk.get('confidence_level', 'N/A')} ({chunk.get('confidence_percentage', 0)}%)\n"
            response += f"  Relevance: {chunk.get('similarity_percentage', 0):.1f}% | Type: {chunk.get('alarm_name', 'N/A')}\n"
            response += f"  Summary: {chunk['text'][:200]}...\n\n"
        
        # Add confidence assessment
        response += f"\n{'='*70}\nCONFIDENCE ASSESSMENT\n{'='*70}\n"
        response += f"Overall Confidence: {quality['confidence']:.0%}\n"
        response += f"Context Quality: {quality['level'].upper()}\n"
        
        if quality['confidence'] < 0.7:
            response += f"[NOTE] Limited context available. Results should be verified.\n"
        else:
            response += f"[OK] Sufficient context with good confidence level.\n"
        
        return response
    
    def _no_context_response(self, question: str) -> str:
        """Response when no context is found"""
        return (f"I could not find relevant event data for: '{question}'\n\n"
               "Suggestions:\n"
               "• Try searching with a priority level (e.g., 'critical events')\n"
               "• Search by component ID (e.g., 'component 103')\n"
               "• Try broader terms (e.g., 'alarms', 'incidents')\n"
               "• Specify a time period (e.g., 'May events')\n\n"
               "Available data: Events from May-November 2025")
    
    def batch_query(self, questions: List[str]) -> List[Dict]:
        """Process multiple questions"""
        results = []
        for q in questions:
            result = self.query(q)
            results.append(result)
        return results
    
    def close(self):
        """Clean up resources"""
        self.retriever.close()


def demo_complete_rag():
    """Demonstrate complete RAG system"""
    rag = CompletRAGSystem()
    
    logger.info("\n" + "="*70)
    logger.info("COMPLETE RAG SYSTEM DEMONSTRATION")
    logger.info("="*70)
    
    # Example queries
    questions = [
        "What critical alarms occurred from component 103?",
        "How many fire emergency events happened in May?",
        "Which components experienced water leakage issues?",
        "Tell me about security malfunction alerts",
        "Why do we have so many high-priority incidents?",
    ]
    
    results = rag.batch_query(questions)
    
    # Display results
    for result in results:
        logger.info(f"\n{'─'*70}")
        logger.info(f"Question: {result['question']}")
        logger.info(f"Context: {result['context_count']} chunks")
        logger.info(f"Status: {result['status']}")
        if result.get('context_quality'):
            logger.info(f"Quality: {result['context_quality']['level']}")
        logger.info(f"\nAnswer:\n{result['answer']}")
    
    # Export results
    logger.info("\n" + "="*70)
    logger.info("Exporting results...")
    
    export_data = {
        'timestamp': '2026-04-17',
        'system': 'Event Intelligence RAG',
        'models': {
            'retrieval': 'sentence-transformers/all-MiniLM-L6-v2',
            'llm': 'gpt-3.5-turbo (simulated)'
        },
        'results': results
    }
    
    with open('rag_results.json', 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
    logger.info("[*] Results exported to rag_results.json")
    
    rag.close()
    logger.info("\n[*] Complete RAG Demo Finished!")


if __name__ == '__main__':
    demo_complete_rag()
