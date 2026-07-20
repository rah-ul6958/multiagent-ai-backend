from datetime import datetime, timedelta

from app.database.models.agent_log import AgentLog
from app.database.models.analytics import DailyAnalytics
from app.database.models.chat_session import ChatSession
from app.database.models.feedback import Feedback
from app.database.models.message import Message
from app.database.models.ticket import Ticket
from app.database.models.user import User
from app.modules.analytics.schema import (
    AgentAnalytics,
    AnalyticsOverview,
    AnalyticsResponse,
    IntentAnalytics,
    TimeSeriesData,
)


class AnalyticsService:
    async def get_analytics(
        self,
        days: int = 30,
    ) -> AnalyticsResponse:
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)
        today_start = now.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        total_conversations = await ChatSession.count()
        total_messages = await Message.count()
        total_users = await User.count()

        conversations_today = await ChatSession.find(
            ChatSession.created_at >= today_start
        ).count()

        messages_today = await Message.find(
            Message.created_at >= today_start
        ).count()

        avg_response = 0.0
        messages_with_latency = (
            await Message.find(
                Message.latency_ms > 0
            )
            .limit(1000)
            .to_list()
        )
        if messages_with_latency:
            avg_response = sum(
                m.latency_ms for m in messages_with_latency
            ) / len(messages_with_latency)

        avg_confidence = 0.0
        messages_with_confidence = (
            await Message.find(
                Message.confidence != None
            )
            .limit(1000)
            .to_list()
        )
        if messages_with_confidence:
            avg_confidence = sum(
                m.confidence
                for m in messages_with_confidence
            ) / len(messages_with_confidence)

        positive = await Feedback.find(
            Feedback.rating == "positive"
        ).count()
        total_feedback = await Feedback.count()
        positive_pct = (
            (positive / total_feedback * 100)
            if total_feedback > 0
            else 0.0
        )

        overview = AnalyticsOverview(
            total_conversations=total_conversations,
            total_messages=total_messages,
            total_users=total_users,
            avg_response_time_ms=avg_response,
            avg_confidence=avg_confidence,
            positive_feedback_pct=positive_pct,
            conversations_today=conversations_today,
            messages_today=messages_today,
        )

        agent_breakdown = await self._get_agent_analytics(
            start_date
        )
        intent_breakdown = await self._get_intent_analytics(
            start_date
        )
        conversation_trend = await self._get_trend(
            start_date, now, "conversations"
        )
        response_time_trend = await self._get_trend(
            start_date, now, "response_time"
        )

        return AnalyticsResponse(
            overview=overview,
            agent_breakdown=agent_breakdown,
            intent_breakdown=intent_breakdown,
            conversation_trend=conversation_trend,
            response_time_trend=response_time_trend,
        )

    async def _get_agent_analytics(
        self, start_date: datetime
    ) -> list[AgentAnalytics]:
        logs = (
            await AgentLog.find(
                AgentLog.created_at >= start_date
            )
            .limit(5000)
            .to_list()
        )

        agent_stats = {}
        for log in logs:
            agent_type = log.agent_type
            if agent_type not in agent_stats:
                agent_stats[agent_type] = {
                    "count": 0,
                    "confidence_sum": 0,
                    "latency_sum": 0,
                    "success_count": 0,
                }
            stats = agent_stats[agent_type]
            stats["count"] += 1
            stats["confidence_sum"] += log.confidence
            stats["latency_sum"] += log.latency_ms
            if log.success:
                stats["success_count"] += 1

        result = []
        for agent_type, stats in agent_stats.items():
            result.append(
                AgentAnalytics(
                    agent_type=agent_type,
                    total_invocations=stats["count"],
                    avg_confidence=stats["confidence_sum"]
                    / stats["count"],
                    avg_latency_ms=stats["latency_sum"]
                    / stats["count"],
                    success_rate=stats["success_count"]
                    / stats["count"]
                    * 100,
                )
            )

        return sorted(
            result,
            key=lambda x: x.total_invocations,
            reverse=True,
        )

    async def _get_intent_analytics(
        self, start_date: datetime
    ) -> list[IntentAnalytics]:
        logs = (
            await AgentLog.find(
                AgentLog.created_at >= start_date,
                AgentLog.intent_detected != None,
            )
            .limit(5000)
            .to_list()
        )

        intent_counts = {}
        for log in logs:
            intent = log.intent_detected
            intent_counts[intent] = (
                intent_counts.get(intent, 0) + 1
            )

        total = sum(intent_counts.values()) or 1

        result = []
        for intent, count in sorted(
            intent_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            result.append(
                IntentAnalytics(
                    intent=intent,
                    count=count,
                    percentage=count / total * 100,
                )
            )

        return result

    async def _get_trend(
        self,
        start_date: datetime,
        end_date: datetime,
        metric: str,
    ) -> list[TimeSeriesData]:
        result = []
        current = start_date.date()
        end = end_date.date()

        while current <= end:
            day_start = datetime.combine(
                current, datetime.min.time()
            )
            day_end = datetime.combine(
                current, datetime.max.time()
            )

            if metric == "conversations":
                value = float(
                    await ChatSession.find(
                        ChatSession.created_at >= day_start,
                        ChatSession.created_at <= day_end,
                    ).count()
                )
            elif metric == "response_time":
                messages = (
                    await Message.find(
                        Message.created_at >= day_start,
                        Message.created_at <= day_end,
                        Message.latency_ms > 0,
                    )
                    .limit(100)
                    .to_list()
                )
                value = (
                    sum(m.latency_ms for m in messages)
                    / len(messages)
                    if messages
                    else 0.0
                )
            else:
                value = 0.0

            result.append(
                TimeSeriesData(
                    date=current.isoformat(),
                    value=round(value, 2),
                )
            )
            current += timedelta(days=1)

        return result
