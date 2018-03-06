#coding:utf-8
import logging
from djcelery.schedulers import DatabaseScheduler, ModelEntry

logger = logging.getLogger(__name__)

class CustomeModelEntry(ModelEntry):
    def is_due(self):
        if not self.model.enabled:
            return False, 5.0
        if self.model.exchange and self.model.total_run_count > 0:
            self.model.enabled = False
            self.model.save()
            logger.info("%s already run once, skip " % self.model.name)
            return False, 5.0
        return self.schedule.is_due(self.last_run_at)

class CustomDatabaseScheduler(DatabaseScheduler):
    Entry = CustomeModelEntry
