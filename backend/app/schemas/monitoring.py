from pydantic import BaseModel


class MonitoringOutboxEvents(BaseModel):
     failed_outbox_events:int