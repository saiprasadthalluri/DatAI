"""OpenTelemetry instrumentation for observability."""
import os
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Cloud Trace exporter - import only when needed
try:
    from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
    CLOUD_TRACE_AVAILABLE = True
except ImportError:
    CLOUD_TRACE_AVAILABLE = False


_tracer_provider: Optional[TracerProvider] = None


def setup_telemetry(app, service_name: str = "chatapp-backend"):
    """
    Set up OpenTelemetry tracing.
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service for tracing
    """
    global _tracer_provider
    
    # Only set up in production or if explicitly enabled
    if os.getenv("ENV") != "production" and not os.getenv("ENABLE_TELEMETRY"):
        return
    
    try:
        resource = Resource.create({"service.name": service_name})
        tracer_provider = TracerProvider(resource=resource)
        
        # Use Cloud Trace exporter in GCP (only if available)
        if os.getenv("PROJECT_ID") and CLOUD_TRACE_AVAILABLE:
            try:
                exporter = CloudTraceSpanExporter(
                    project_id=os.getenv("PROJECT_ID")
                )
                tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
            except Exception as e:
                import logging
                logging.warning(f"Failed to set up Cloud Trace exporter: {e}, falling back to console")
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter
                tracer_provider.add_span_processor(
                    BatchSpanProcessor(ConsoleSpanExporter())
                )
        else:
            # Fallback to console exporter for local dev
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            tracer_provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )
        
        trace.set_tracer_provider(tracer_provider)
        _tracer_provider = tracer_provider
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument()
        
        # Instrument HTTPX (for external API calls)
        HTTPXClientInstrumentor().instrument()
        
    except Exception as e:
        # Fail gracefully if telemetry setup fails
        import logging
        logging.warning(f"Failed to set up telemetry: {e}")


def get_tracer(name: str):
    """Get a tracer instance."""
    return trace.get_tracer(name)


