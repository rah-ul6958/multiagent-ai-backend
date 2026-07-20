import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from app.database.models.agent_log import AgentLog
from app.database.models.analytics import DailyAnalytics
from app.database.models.chat_session import ChatSession
from app.database.models.document import DocumentMetadata
from app.database.models.feedback import Feedback
from app.database.models.message import Message
from app.database.models.ticket import Ticket
from app.database.models.user import User
from app.core.config import settings

CONFIG_OVERRIDE_PATH = Path(__file__).parent.parent.parent / "config_override.json"

_start_time = time.time()
logger = logging.getLogger(__name__)


class AdminService:
    async def get_dashboard(self) -> dict:
        try:
            now = datetime.utcnow()
            today_start = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            total_users = await User.count()
            today_messages = (
                await Message.find(
                    Message.created_at >= today_start
                ).to_list()
            )
            active_users_today = len({m.session_id for m in today_messages})

            total_sessions = await ChatSession.count()
            active_sessions = await ChatSession.find(
                ChatSession.status == "active"
            ).count()

            messages_today = await Message.find(
                Message.created_at >= today_start
            ).count()

            total_documents = await DocumentMetadata.count()
            ready_documents = await DocumentMetadata.find(
                DocumentMetadata.status == "ready"
            ).count()

            total_tickets = await Ticket.count()
            open_tickets = await Ticket.find(
                Ticket.status == "open"
            ).count()
            closed_tickets = await Ticket.find(
                Ticket.status == "closed"
            ).count()
            resolved_tickets = await Ticket.find(
                Ticket.status == "resolved"
            ).count()

            total_feedback = await Feedback.count()
            positive_feedback = await Feedback.find(
                Feedback.rating == "positive"
            ).count()

            avg_latency = 0.0
            msgs_with_latency = (
                await Message.find(
                    Message.latency_ms > 0
                )
                .limit(500)
                .to_list()
            )
            if msgs_with_latency:
                avg_latency = sum(
                    m.latency_ms for m in msgs_with_latency
                ) / len(msgs_with_latency)

            total_tokens = 0
            msgs_with_tokens = (
                await Message.find(
                    Message.tokens_used > 0
                )
                .limit(500)
                .to_list()
            )
            if msgs_with_tokens:
                total_tokens = sum(
                    m.tokens_used for m in msgs_with_tokens
                )

            total_embeddings = 0
            for doc in await DocumentMetadata.find(
                DocumentMetadata.status == "ready"
            ).to_list():
                total_embeddings += doc.chunk_count

            satisfaction_score = (
                (positive_feedback / total_feedback * 100)
                if total_feedback > 0
                else 0.0
            )

            resolution_rate = (
                ((resolved_tickets + closed_tickets) / total_tickets * 100)
                if total_tickets > 0
                else 0.0
            )

            conversations_per_day = []
            for i in range(7):
                day = now - timedelta(days=6 - i)
                day_start = day.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                day_end = day_start + timedelta(days=1)
                count = await ChatSession.find(
                    ChatSession.created_at >= day_start,
                    ChatSession.created_at < day_end,
                ).count()
                conversations_per_day.append({
                    "date": day_start.strftime("%Y-%m-%d"),
                    "count": count,
                })

            users_per_day = []
            for i in range(7):
                day = now - timedelta(days=6 - i)
                day_start = day.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                day_end = day_start + timedelta(days=1)
                count = await User.find(
                    User.created_at >= day_start,
                    User.created_at < day_end,
                ).count()
                users_per_day.append({
                    "date": day_start.strftime("%Y-%m-%d"),
                    "count": count,
                })

            agent_usage = {}
            recent_logs = (
                await AgentLog.find_all()
                .sort("-created_at")
                .limit(500)
                .to_list()
            )
            for log in recent_logs:
                agent = log.agent_type
                agent_usage[agent] = (
                    agent_usage.get(agent, 0) + 1
                )

            intent_dist = {}
            for log in recent_logs:
                if log.intent_detected:
                    intent = log.intent_detected
                    intent_dist[intent] = (
                        intent_dist.get(intent, 0) + 1
                    )

            response_trend = []
            for i in range(7):
                day = now - timedelta(days=6 - i)
                day_start = day.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                day_end = day_start + timedelta(days=1)
                msgs = (
                    await Message.find(
                        Message.created_at >= day_start,
                        Message.created_at < day_end,
                        Message.latency_ms > 0,
                    )
                    .limit(100)
                    .to_list()
                )
                avg = (
                    sum(m.latency_ms for m in msgs) / len(msgs)
                    if msgs
                    else 0.0
                )
                response_trend.append({
                    "date": day_start.strftime("%Y-%m-%d"),
                    "avg_latency_ms": round(avg, 2),
                })

            recent_activity = []
            for session in (
                await ChatSession.find_all()
                .sort("-updated_at")
                .limit(10)
                .to_list()
            ):
                msg_count = await Message.find(
                    Message.session_id == str(session.id)
                ).count()
                recent_activity.append({
                    "session_id": str(session.id),
                    "title": session.title,
                    "user_id": session.user_id,
                    "message_count": msg_count,
                    "updated_at": session.updated_at.isoformat(),
                })

            return {
                "kpis": {
                    "total_users": total_users,
                    "active_users_today": active_users_today,
                    "total_conversations": total_sessions,
                    "active_chat_sessions": active_sessions,
                    "ai_requests_today": messages_today,
                    "avg_response_time_ms": round(avg_latency, 2),
                    "avg_retrieval_time_ms": round(avg_latency * 0.3, 2),
                    "avg_llm_latency_ms": round(avg_latency * 0.7, 2),
                    "satisfaction_score": round(satisfaction_score, 1),
                    "resolution_rate": round(resolution_rate, 1),
                    "open_tickets": open_tickets,
                    "closed_tickets": closed_tickets,
                    "total_documents": total_documents,
                    "indexed_documents": ready_documents,
                    "total_embeddings": total_embeddings,
                    "total_tokens_used": total_tokens,
                    "api_cost_estimation": round(total_tokens * 0.000002, 4),
                },
                "charts": {
                    "conversations_per_day": conversations_per_day,
                    "users_per_day": users_per_day,
                    "agent_usage_distribution": [
                        {"agent": k, "count": v}
                        for k, v in sorted(
                            agent_usage.items(),
                            key=lambda x: x[1],
                            reverse=True,
                        )
                    ],
                    "intent_distribution": [
                        {"intent": k, "count": v}
                        for k, v in sorted(
                            intent_dist.items(),
                            key=lambda x: x[1],
                            reverse=True,
                        )
                    ],
                    "response_time_trend": response_trend,
                },
                "recent_activity": recent_activity,
            }
        except Exception as exc:
            logger.exception("Dashboard metrics unavailable: %s", exc)
            return {
                "kpis": {
                    "total_users": 0,
                    "active_users_today": 0,
                    "total_conversations": 0,
                    "active_chat_sessions": 0,
                    "ai_requests_today": 0,
                    "avg_response_time_ms": 0.0,
                    "avg_retrieval_time_ms": 0.0,
                    "avg_llm_latency_ms": 0.0,
                    "satisfaction_score": 0.0,
                    "resolution_rate": 0.0,
                    "open_tickets": 0,
                    "closed_tickets": 0,
                    "total_documents": 0,
                    "indexed_documents": 0,
                    "total_embeddings": 0,
                    "total_tokens_used": 0,
                    "api_cost_estimation": 0.0,
                },
                "charts": {
                    "conversations_per_day": [],
                    "users_per_day": [],
                    "agent_usage_distribution": [],
                    "intent_distribution": [],
                    "response_time_trend": [],
                },
                "recent_activity": [],
            }

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 50,
        search: str = None,
        role: str = None,
        status: str = None,
    ) -> dict:
        query = {}
        if search:
            query["$or"] = [
                {"full_name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
            ]
        if role:
            query["role"] = role
        if status == "active":
            query["is_active"] = True
        elif status == "inactive":
            query["is_active"] = False

        users = (
            await User.find(query)
            .sort("-created_at")
            .skip(skip)
            .limit(limit)
            .to_list()
        )
        total = await User.find(query).count()

        result = []
        for u in users:
            user_sessions = await ChatSession.find(
                ChatSession.user_id == str(u.id)
            ).to_list()
            session_ids = [str(s.id) for s in user_sessions]
            session_count = len(user_sessions)
            msg_count = 0
            if session_ids:
                msg_count = await Message.find(
                    Message.session_id.in_(session_ids)
                ).count()

            result.append({
                "id": str(u.id),
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "session_count": session_count,
                "message_count": msg_count,
            })

        return {"users": result, "total": total}

    async def update_user(
        self,
        user_id: str,
        role: str = None,
        is_active: bool = None,
    ) -> dict:
        user = await User.get(user_id)
        if not user:
            return None
        if role:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        user.updated_at = datetime.utcnow()
        await user.save()
        return {
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        }

    async def delete_user(self, user_id: str) -> bool:
        user = await User.get(user_id)
        if not user:
            return False
        sessions = await ChatSession.find(
            ChatSession.user_id == user_id
        ).to_list()
        for s in sessions:
            await Message.delete_many(
                Message.session_id == str(s.id)
            )
            await s.delete()
        await user.delete()
        return True

    async def get_conversations(
        self,
        skip: int = 0,
        limit: int = 50,
        user_id: str = None,
        intent: str = None,
        search: str = None,
    ) -> dict:
        query = {}
        if user_id:
            query["user_id"] = user_id
        if search:
            query["title"] = {
                "$regex": search,
                "$options": "i",
            }

        sessions = (
            await ChatSession.find(query)
            .sort("-updated_at")
            .skip(skip)
            .limit(limit)
            .to_list()
        )
        total = await ChatSession.find(query).count()

        result = []
        for s in sessions:
            msg_count = await Message.find(
                Message.session_id == str(s.id)
            ).count()

            result.append({
                "id": str(s.id),
                "title": s.title,
                "user_id": s.user_id,
                "status": s.status,
                "agent_type": s.agent_type,
                "message_count": msg_count,
                "total_tokens": 0,
                "avg_latency_ms": 0,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            })

        return {"conversations": result, "total": total}

    async def get_conversation_detail(
        self, session_id: str
    ) -> dict:
        session = await ChatSession.get(session_id)
        if not session:
            return None

        messages = (
            await Message.find(
                Message.session_id == session_id
            )
            .sort("created_at")
            .to_list()
        )

        agent_logs = (
            await AgentLog.find(
                AgentLog.session_id == session_id
            )
            .sort("created_at")
            .to_list()
        )

        return {
            "session": {
                "id": str(session.id),
                "title": session.title,
                "user_id": session.user_id,
                "status": session.status,
                "agent_type": session.agent_type,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
            },
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "agent_type": m.agent_type,
                    "confidence": m.confidence,
                    "sources": m.sources,
                    "tokens_used": m.tokens_used,
                    "latency_ms": m.latency_ms,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
            "agent_logs": [
                {
                    "id": str(l.id),
                    "agent_type": l.agent_type,
                    "intent_detected": l.intent_detected,
                    "tools_used": l.tools_used,
                    "tokens_used": l.tokens_used,
                    "latency_ms": l.latency_ms,
                    "confidence": l.confidence,
                    "success": l.success,
                    "error_message": l.error_message,
                    "created_at": l.created_at.isoformat(),
                }
                for l in agent_logs
            ],
        }

    async def delete_conversation(
        self, session_id: str
    ) -> bool:
        session = await ChatSession.get(session_id)
        if not session:
            return False
        await Message.delete_many(
            Message.session_id == session_id
        )
        await AgentLog.delete_many(
            AgentLog.session_id == session_id
        )
        await session.delete()
        return True

    async def _get_agent_status(self) -> list:
        agent_names = [
            "intent_detection", "billing", "technical_support",
            "product", "complaint", "faq", "rag_retrieval", "validation",
        ]
        result = []
        for name in agent_names:
            logs = (
                await AgentLog.find(AgentLog.agent_type == name)
                .sort("-created_at")
                .limit(100)
                .to_list()
            )
            total = len(logs)
            if total == 0:
                result.append({
                    "name": name, "status": "idle",
                    "latency_ms": 0, "confidence": 0, "health": "healthy",
                })
                continue
            avg_lat = sum(l.latency_ms for l in logs) / total
            avg_conf = sum(l.confidence for l in logs) / total
            success_rate = sum(1 for l in logs if l.success) / total
            health = "healthy" if success_rate >= 0.8 else "degraded" if success_rate >= 0.5 else "critical"
            result.append({
                "name": name, "status": "active",
                "latency_ms": round(avg_lat, 2),
                "confidence": round(avg_conf, 3),
                "health": health,
            })
        return result

    async def get_activity_panel(self) -> dict:
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            recent_sessions = (
                await ChatSession.find_all()
                .sort("-updated_at")
                .limit(5)
                .to_list()
            )

            recent_chats = []
            for s in recent_sessions:
                user = await User.get(s.user_id)
                recent_chats.append({
                    "id": str(s.id),
                    "title": s.title[:40] + "..." if len(s.title) > 40 else s.title,
                    "user_name": user.full_name if user else "Unknown",
                    "agent_type": s.agent_type or "pending",
                    "updated_at": s.updated_at.isoformat(),
                })

            total_tokens = 0
            msgs_with_tokens = (
                await Message.find(Message.tokens_used > 0)
                .limit(500)
                .to_list()
            )
            if msgs_with_tokens:
                total_tokens = sum(m.tokens_used for m in msgs_with_tokens)

            avg_latency = 0.0
            msgs_with_latency = (
                await Message.find(Message.latency_ms > 0)
                .limit(500)
                .to_list()
            )
            if msgs_with_latency:
                avg_latency = sum(m.latency_ms for m in msgs_with_latency) / len(msgs_with_latency)

            messages_today = await Message.find(
                Message.created_at >= today_start
            ).count()

            active_users_today = len(
                {m.session_id for m in await Message.find(
                    Message.created_at >= today_start
                ).to_list()}
            )

            provider_status = {
                "groq": "online" if settings.GROQ_API_KEY else "offline",
                "gemini": "online" if settings.GEMINI_API_KEY else "offline",
                "openrouter": "online" if settings.OPENROUTER_API_KEY else "offline",
            }

            primary_provider = "groq" if settings.GROQ_API_KEY else "gemini" if settings.GEMINI_API_KEY else "none"

            return {
                "recent_chats": recent_chats,
                "usage": {
                    "tokens": total_tokens,
                    "messages_today": messages_today,
                    "avg_latency_ms": round(avg_latency, 2),
                    "active_users_today": active_users_today,
                },
                "provider": {
                    "primary": primary_provider,
                    "model": settings.AI_PRIMARY_MODEL if primary_provider == "groq" else settings.AI_FALLBACK_MODEL,
                    "status": provider_status,
                },
                "agents": await self._get_agent_status(),
            }
        except Exception as exc:
            logger.exception("Activity panel error: %s", exc)
            return {
                "recent_chats": [],
                "usage": {"tokens": 0, "messages_today": 0, "avg_latency_ms": 0, "active_users_today": 0},
                "provider": {"primary": "unknown", "model": "unknown", "status": {}},
                "agents": [],
            }

    async def get_agent_monitoring(self) -> dict:
        agent_configs = {
            "intent_detection": {
                "category": "routing",
                "description": "Classifies user messages into billing, technical, product, complaint, or FAQ intents using LLM-based classification.",
                "model": "LLM classifier",
            },
            "billing": {
                "category": "domain",
                "description": "Handles payment issues, invoices, refunds, subscriptions, and pricing questions with context-aware responses.",
                "model": settings.AI_PRIMARY_MODEL,
            },
            "technical_support": {
                "category": "domain",
                "description": "Resolves bugs, errors, crashes, installation issues, and configuration troubleshooting.",
                "model": settings.AI_PRIMARY_MODEL,
            },
            "product": {
                "category": "domain",
                "description": "Provides product information, feature comparisons, specifications, and recommendations.",
                "model": settings.AI_PRIMARY_MODEL,
            },
            "complaint": {
                "category": "domain",
                "description": "Manages customer complaints, dissatisfaction, and escalation requests with empathetic responses.",
                "model": settings.AI_PRIMARY_MODEL,
            },
            "faq": {
                "category": "domain",
                "description": "Answers frequently asked questions using knowledge base retrieval and general knowledge.",
                "model": settings.AI_PRIMARY_MODEL,
            },
            "memory": {
                "category": "specialized",
                "description": "Maintains conversation context and summaries across multi-turn interactions for continuity.",
                "model": settings.AI_PRIMARY_MODEL,
            },
            "rag_retrieval": {
                "category": "specialized",
                "description": "Performs hybrid search (dense + sparse) across the knowledge base to retrieve relevant documents.",
                "model": "BAAI/bge-small-en-v1.5 + BM25",
            },
            "validation": {
                "category": "specialized",
                "description": "Validates AI responses for accuracy, completeness, and policy compliance before returning to user.",
                "model": settings.AI_PRIMARY_MODEL,
            },
        }

        agents = list(agent_configs.keys())
        result = []

        for agent_name in agents:
            config = agent_configs[agent_name]
            logs = (
                await AgentLog.find(
                    AgentLog.agent_type == agent_name
                )
                .sort("-created_at")
                .limit(1000)
                .to_list()
            )

            total_exec = len(logs)
            success = sum(1 for l in logs if l.success)
            failures = total_exec - success
            avg_lat = (
                sum(l.latency_ms for l in logs) / total_exec
                if total_exec > 0
                else 0
            )
            avg_conf = (
                sum(l.confidence for l in logs) / total_exec
                if total_exec > 0
                else 0
            )
            last_exec = (
                logs[0].created_at.isoformat()
                if logs
                else None
            )
            total_tokens = sum(l.tokens_used for l in logs)

            health = "healthy"
            if total_exec > 0:
                success_rate = success / total_exec
                if success_rate < 0.5:
                    health = "critical"
                elif success_rate < 0.8:
                    health = "degraded"

            recent_errors = [
                {
                    "message": l.error_message or "Unknown error",
                    "input": l.input_text[:100] if l.input_text else "",
                    "timestamp": l.created_at.isoformat(),
                }
                for l in logs
                if not l.success and l.error_message
            ][:5]

            recent_executions = [
                {
                    "input": l.input_text[:120] if l.input_text else "",
                    "output": l.output_text[:120] if l.output_text else "",
                    "latency_ms": round(l.latency_ms, 2),
                    "confidence": round(l.confidence, 3),
                    "success": l.success,
                    "timestamp": l.created_at.isoformat(),
                }
                for l in logs
            ][:10]

            latency_trend = []
            for i in range(7):
                from datetime import timedelta
                now = datetime.utcnow()
                day = now - timedelta(days=6 - i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                day_logs = [
                    l for l in logs
                    if day_start <= l.created_at < day_end
                ]
                if day_logs:
                    avg = sum(l.latency_ms for l in day_logs) / len(day_logs)
                    latency_trend.append({
                        "date": day_start.strftime("%Y-%m-%d"),
                        "avg_latency_ms": round(avg, 2),
                        "count": len(day_logs),
                    })
                else:
                    latency_trend.append({
                        "date": day_start.strftime("%Y-%m-%d"),
                        "avg_latency_ms": 0,
                        "count": 0,
                    })

            result.append({
                "name": agent_name,
                "category": config["category"],
                "description": config["description"],
                "model": config["model"],
                "status": "active" if total_exec > 0 else "idle",
                "total_executions": total_exec,
                "success_count": success,
                "failure_count": failures,
                "success_rate": round(
                    (success / total_exec * 100) if total_exec > 0 else 0,
                    1,
                ),
                "failure_rate": round(
                    (failures / total_exec * 100) if total_exec > 0 else 0,
                    1,
                ),
                "avg_latency_ms": round(avg_lat, 2),
                "avg_confidence": round(avg_conf, 3),
                "total_tokens": total_tokens,
                "last_execution": last_exec,
                "health": health,
                "recent_errors": recent_errors,
                "recent_executions": recent_executions,
                "latency_trend": latency_trend,
            })

        summary = {
            "total_agents": len(result),
            "active_agents": sum(1 for a in result if a["status"] == "active"),
            "total_executions": sum(a["total_executions"] for a in result),
            "total_tokens": sum(a["total_tokens"] for a in result),
            "avg_success_rate": round(
                sum(a["success_rate"] for a in result if a["total_executions"] > 0)
                / max(sum(1 for a in result if a["total_executions"] > 0), 1),
                1,
            ),
            "avg_latency_ms": round(
                sum(a["avg_latency_ms"] * a["total_executions"] for a in result)
                / max(sum(a["total_executions"] for a in result), 1),
                2,
            ),
        }

        return {"summary": summary, "agents": result}

    async def get_vector_db_stats(self) -> dict:
        try:
            from app.ai.rag.vector_store import (
                VectorStoreService,
            )

            vs = VectorStoreService()
            stats = vs.get_stats()
        except Exception:
            logger.warning("Failed to load vector DB stats", exc_info=True)
            stats = {
                "total_vectors": 0,
                "total_documents": 0,
            }

        total_chunks = 0
        docs = await DocumentMetadata.find(
            DocumentMetadata.status == "ready"
        ).to_list()
        for doc in docs:
            total_chunks += doc.chunk_count

        return {
            "total_vectors": stats.get("total_vectors", 0),
            "total_documents": stats.get("total_documents", 0),
            "embedding_model": "BAAI/bge-small-en-v1.5",
            "chunk_count": total_chunks,
            "avg_chunk_size": 512,
            "last_indexing_time": (
                docs[-1].updated_at.isoformat()
                if docs
                else None
            ),
        }

    async def get_logs(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        logs = (
            await AgentLog.find_all()
            .sort("-created_at")
            .skip(skip)
            .limit(limit)
            .to_list()
        )
        total = await AgentLog.count()

        result = []
        for log in logs:
            result.append({
                "id": str(log.id),
                "session_id": log.session_id,
                "agent_type": log.agent_type,
                "intent_detected": log.intent_detected,
                "input_text": log.input_text[:200] if log.input_text else "",
                "output_text": log.output_text[:200] if log.output_text else "",
                "success": log.success,
                "error_message": log.error_message,
                "latency_ms": round(log.latency_ms, 2),
                "confidence": round(log.confidence, 3),
                "tokens_used": log.tokens_used,
                "tools_used": log.tools_used,
                "created_at": log.created_at.isoformat(),
            })

        return {"logs": result, "total": total}

    def get_settings(self) -> dict:
        return {
            "provider": settings.AI_FALLBACK_PROVIDER,
            "primary_model": settings.AI_PRIMARY_MODEL,
            "fallback_model": settings.AI_FALLBACK_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "top_k_retrieval": settings.TOP_K_RETRIEVAL,
            "top_k_rerank": settings.TOP_K_RERANK,
            "temperature": settings.TEMPERATURE,
            "max_tokens": settings.AI_MAX_TOKENS,
            "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "log_level": settings.LOG_LEVEL,
            "debug": settings.DEBUG,
            "api_keys": {
                "gemini": bool(settings.GEMINI_API_KEY),
                "groq": bool(settings.GROQ_API_KEY),
                "openrouter": bool(settings.OPENROUTER_API_KEY),
            },
        }

    def update_settings(self, updates: dict) -> dict:
        existing = {}
        if CONFIG_OVERRIDE_PATH.exists():
            existing = json.loads(CONFIG_OVERRIDE_PATH.read_text())

        api_key_map = {
            "gemini_api_key": "GEMINI_API_KEY",
            "groq_api_key": "GROQ_API_KEY",
            "openrouter_api_key": "OPENROUTER_API_KEY",
        }
        env_overrides = {}
        for k, v in list(updates.items()):
            if k in api_key_map and v is not None:
                env_overrides[api_key_map[k]] = v
                updates.pop(k)
            elif k == "temperature" and v is not None:
                updates["TEMPERATURE"] = v
                updates.pop(k)
            elif k == "max_tokens" and v is not None:
                updates["AI_MAX_TOKENS"] = v
                updates.pop(k)

        existing.update({k: v for k, v in updates.items() if v is not None})
        CONFIG_OVERRIDE_PATH.write_text(json.dumps(existing, indent=2))

        if env_overrides:
            env_path = Path(__file__).parent.parent.parent / ".env"
            env_lines = env_path.read_text().splitlines() if env_path.exists() else []
            env_dict = {}
            for line in env_lines:
                if "=" in line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    env_dict[key.strip()] = val.strip()
            env_dict.update(env_overrides)
            env_path.write_text("\n".join(f"{k}={v}" for k, v in env_dict.items()) + "\n")
            from app.core.config import get_settings
            get_settings.cache_clear()

        return self.get_settings()


admin_service = AdminService()
