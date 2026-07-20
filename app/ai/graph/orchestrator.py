import json
import logging
import time
from typing import Annotated, Any, TypedDict

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.ai.agents.domain import (
    BillingAgent,
    ComplaintAgent,
    FAQAgent,
    ProductAgent,
    TechnicalSupportAgent,
)
from app.ai.agents.intent import IntentDetectionAgent
from app.ai.agents.specialized import (
    ConversationMemoryAgent,
    RAGRetrievalAgent,
    ResponseValidationAgent,
)
from app.ai.llm.service import llm_service

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the multi-agent graph."""

    messages: Annotated[list, add_messages]
    user_message: str
    session_id: str
    user_id: str
    intent: str
    intent_confidence: float
    retrieved_documents: list
    memory_summary: str
    agent_response: str
    agent_type: str
    final_response: str
    validated: bool
    validation_issues: list
    provider: str
    model: str
    latency_ms: float


class OrchestratorGraph:
    """LangGraph-based multi-agent orchestrator."""

    def __init__(self, trace_callback=None):
        self.intent_agent = IntentDetectionAgent()
        self.billing_agent = BillingAgent()
        self.technical_agent = TechnicalSupportAgent()
        self.product_agent = ProductAgent()
        self.complaint_agent = ComplaintAgent()
        self.faq_agent = FAQAgent()
        self.rag_agent = RAGRetrievalAgent()
        self.memory_agent = ConversationMemoryAgent()
        self.validation_agent = ResponseValidationAgent()
        self._trace_callback = trace_callback
        self._session_id = ""
        self._message_id = ""
        self._user_message = ""
        self._agent_response = ""

        self.agent_map = {
            "billing": self.billing_agent,
            "technical_support": self.technical_agent,
            "product": self.product_agent,
            "complaint": self.complaint_agent,
            "faq": self.faq_agent,
        }

        self.graph = self._build_graph()

    def _emit_trace(self, step: str, status: str, message: str, latency_ms: float = 0, details: dict = None):
        if self._trace_callback:
            try:
                import asyncio
                event = {
                    "type": "trace",
                    "step": step,
                    "status": status,
                    "message": message,
                    "latency_ms": round(latency_ms, 1),
                    "details": details or {},
                }
                loop = asyncio.get_running_loop()
                loop.create_task(self._trace_callback(event))
            except RuntimeError:
                pass

        if status == "complete" and self._session_id:
            try:
                import asyncio
                loop = asyncio.get_running_loop()
                loop.create_task(self._log_agent_step(step, latency_ms, details or {}))
            except RuntimeError:
                pass

    async def _log_agent_step(self, step: str, latency_ms: float, details: dict):
        try:
            from app.database.models.agent_log import AgentLog
            intent = details.get("intent", step)
            confidence = details.get("confidence", 0.95)
            is_valid = details.get("valid", True)

            log = AgentLog(
                session_id=self._session_id,
                message_id=self._message_id,
                agent_type=step,
                intent_detected=intent if step == "intent_detection" else None,
                input_text=self._user_message[:500] if self._user_message else "",
                output_text=self._agent_response[:500] if self._agent_response else "",
                tokens_used=0,
                latency_ms=round(latency_ms, 2),
                confidence=confidence if step == "intent_detection" else (1.0 if is_valid else 0.5),
                success=True,
            )
            await log.insert()
        except Exception:
            logger.debug("Failed to log agent step", exc_info=True)

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        workflow.add_node(
            "memory_retrieval", self._memory_node
        )
        workflow.add_node(
            "rag_retrieval", self._rag_node
        )
        workflow.add_node(
            "intent_detection", self._intent_node
        )
        workflow.add_node(
            "route_to_agent", self._routing_node
        )
        workflow.add_node(
            "billing_agent", self._billing_node
        )
        workflow.add_node(
            "technical_agent", self._technical_node
        )
        workflow.add_node(
            "product_agent", self._product_node
        )
        workflow.add_node(
            "complaint_agent", self._complaint_node
        )
        workflow.add_node("faq_agent", self._faq_node)
        workflow.add_node(
            "response_validation", self._validation_node
        )
        workflow.add_node(
            "compile_response", self._compile_node
        )

        workflow.set_entry_point("memory_retrieval")
        workflow.add_edge(
            "memory_retrieval", "rag_retrieval"
        )
        workflow.add_edge(
            "rag_retrieval", "intent_detection"
        )
        workflow.add_edge(
            "intent_detection", "route_to_agent"
        )

        workflow.add_conditional_edges(
            "route_to_agent",
            self._route_intent,
            {
                "billing": "billing_agent",
                "technical_support": "technical_agent",
                "product": "product_agent",
                "complaint": "complaint_agent",
                "faq": "faq_agent",
            },
        )

        workflow.add_edge(
            "billing_agent", "response_validation"
        )
        workflow.add_edge(
            "technical_agent", "response_validation"
        )
        workflow.add_edge(
            "product_agent", "response_validation"
        )
        workflow.add_edge(
            "complaint_agent", "response_validation"
        )
        workflow.add_edge(
            "faq_agent", "response_validation"
        )
        workflow.add_edge(
            "response_validation", "compile_response"
        )
        workflow.add_edge("compile_response", END)

        return workflow.compile()

    async def _memory_node(
        self, state: AgentState
    ) -> dict:
        t0 = time.time()
        self._emit_trace("memory_retrieval", "running", "Fetching conversation history...")
        result = await self.memory_agent.process(
            state["user_message"],
            context={"session_id": state["session_id"]},
        )
        latency = (time.time() - t0) * 1000
        self._emit_trace("memory_retrieval", "complete", f"Retrieved context ({latency:.0f}ms)", latency_ms=latency)
        return {
            "memory_summary": result.get("summary", ""),
        }

    async def _rag_node(
        self, state: AgentState
    ) -> dict:
        t0 = time.time()
        self._emit_trace("rag_retrieval", "running", "Searching knowledge base...")
        result = await self.rag_agent.process(
            state["user_message"],
            context={"session_id": state["session_id"]},
        )
        doc_count = len(result.get("documents", []))
        latency = (time.time() - t0) * 1000
        self._emit_trace("rag_retrieval", "complete", f"Found {doc_count} documents ({latency:.0f}ms)", latency_ms=latency, details={"doc_count": doc_count})
        return {
            "retrieved_documents": result.get(
                "documents", []
            ),
        }

    async def _intent_node(
        self, state: AgentState
    ) -> dict:
        t0 = time.time()
        self._emit_trace("intent_detection", "running", "Classifying user intent...")
        context = {
            "conversation_history": state.get(
                "messages", []
            )[-5:],
            "retrieved_documents": state.get(
                "retrieved_documents", []
            ),
        }

        result = await self.intent_agent.process(
            state["user_message"], context
        )
        latency = (time.time() - t0) * 1000
        intent = result.get("intent", "faq")
        confidence = result.get("confidence", 0.5)
        self._emit_trace("intent_detection", "complete", f"Intent: {intent} ({confidence:.0%})", latency_ms=latency, details={"intent": intent, "confidence": confidence})
        return {
            "intent": intent,
            "intent_confidence": confidence,
        }

    async def _routing_node(
        self, state: AgentState
    ) -> dict:
        intent = state.get("intent", "faq")
        self._emit_trace("route_to_agent", "complete", f"Routed to {intent} agent")
        return {
            "agent_type": intent
        }

    def _route_intent(self, state: AgentState) -> str:
        intent = state.get("intent", "faq")
        if intent in self.agent_map:
            return intent
        return "faq"

    async def _generate_agent_response(
        self,
        agent,
        state: AgentState,
        agent_name: str = "agent",
    ) -> dict:
        t0 = time.time()
        self._emit_trace(agent_name, "running", f"Generating response with {agent_name}...")
        context = {
            "session_id": state["session_id"],
            "conversation_history": state.get(
                "messages", []
            )[-5:],
            "retrieved_documents": state.get(
                "retrieved_documents", []
            ),
            "memory_summary": state.get(
                "memory_summary", ""
            ),
        }

        result = await agent.process(
            state["user_message"], context
        )
        latency = (time.time() - t0) * 1000
        self._agent_response = result.get("response", "")
        self._emit_trace(agent_name, "complete", f"Response generated ({latency:.0f}ms)", latency_ms=latency)

        return {
            "agent_response": result.get(
                "response", ""
            ),
            "provider": result.get(
                "provider", "unknown"
            ),
            "model": result.get("model", "unknown"),
        }

    async def _billing_node(
        self, state: AgentState
    ) -> dict:
        return await self._generate_agent_response(
            self.billing_agent, state, "billing_agent"
        )

    async def _technical_node(
        self, state: AgentState
    ) -> dict:
        return await self._generate_agent_response(
            self.technical_agent, state, "technical_agent"
        )

    async def _product_node(
        self, state: AgentState
    ) -> dict:
        return await self._generate_agent_response(
            self.product_agent, state, "product_agent"
        )

    async def _complaint_node(
        self, state: AgentState
    ) -> dict:
        return await self._generate_agent_response(
            self.complaint_agent, state, "complaint_agent"
        )

    async def _faq_node(
        self, state: AgentState
    ) -> dict:
        return await self._generate_agent_response(
            self.faq_agent, state, "faq_agent"
        )

    async def _validation_node(
        self, state: AgentState
    ) -> dict:
        t0 = time.time()
        self._emit_trace("response_validation", "running", "Validating response quality...")
        result = await self.validation_agent.process(
            state.get("agent_response", ""),
            context={
                "response": state.get(
                    "agent_response", ""
                ),
                "agent_type": state.get(
                    "agent_type", "general"
                ),
            },
        )
        latency = (time.time() - t0) * 1000
        is_valid = result.get("is_valid", True)
        self._emit_trace("response_validation", "complete", f"{'Passed' if is_valid else 'Issues found'} ({latency:.0f}ms)", latency_ms=latency, details={"valid": is_valid})
        return {
            "final_response": result.get(
                "response", state.get("agent_response", "")
            ),
            "validated": is_valid,
            "validation_issues": result.get(
                "issues", []
            ),
        }

    async def _compile_node(
        self, state: AgentState
    ) -> dict:
        self._emit_trace("compile_response", "complete", "Response ready")
        final = state.get("final_response", "")
        if not final:
            final = state.get(
                "agent_response",
                "I apologize, but I could not generate a response.",
            )
        return {"final_response": final}

    async def process(
        self,
        message: str,
        conversation_history: list = None,
        session_id: str = "",
        user_id: str = "",
        message_id: str = "",
    ):
        start_time = time.time()
        self._session_id = session_id
        self._message_id = message_id
        self._user_message = message
        self._agent_response = ""

        initial_state: AgentState = {
            "messages": [],
            "user_message": message,
            "session_id": session_id,
            "user_id": user_id,
            "intent": "",
            "intent_confidence": 0.0,
            "retrieved_documents": [],
            "memory_summary": "",
            "agent_response": "",
            "agent_type": "",
            "final_response": "",
            "validated": False,
            "validation_issues": [],
            "provider": "",
            "model": "",
            "latency_ms": 0.0,
        }

        yield {
            "type": "metadata",
            "content": "",
            "agent_type": "processing",
        }

        try:
            result = await self.graph.ainvoke(
                initial_state
            )

            final_response = result.get(
                "final_response", ""
            )
            agent_type = result.get(
                "agent_type", "faq"
            )
            sources = result.get(
                "retrieved_documents", []
            )[:3]

            yield {
                "type": "metadata",
                "content": "",
                "agent_type": agent_type,
                "sources": [
                    {
                        "content": s.get("text", "")[:200],
                        "score": s.get("score", 0),
                    }
                    for s in sources
                ],
            }

            words = final_response.split()
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i : i + 3])
                yield {
                    "type": "token",
                    "content": chunk + " ",
                    "agent_type": agent_type,
                }

            latency_ms = (
                time.time() - start_time
            ) * 1000

            logger.info(
                f"Graph completed: intent={agent_type}, "
                f"confidence={result.get('intent_confidence', 0):.2f}, "
                f"provider={result.get('provider', 'unknown')}, "
                f"latency={latency_ms:.0f}ms"
            )

        except Exception as e:
            logger.error(f"Graph execution error: {e}")
            yield {
                "type": "error",
                "content": str(e),
                "agent_type": "error",
            }
