import logging
from robocorp import workitems
from robocorp.tasks import task
from news_automation import NewsAutomation
from business_exception import BusinessException

logging.basicConfig(format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@task
def consume_news_workitems():
    """Consumes news work items, executes news extraction for each item, marks them as done or failed."""

    automation = NewsAutomation()

    for item in workitems.inputs:
        try:
            automation.setup_extraction(item)
            automation.execute_news_extraction()
            automation.create_output_files()
            item.done()
        except Exception as e:
            handle_exception(item, e)
        finally:
            automation.close_resources()


def handle_exception(item: workitems.Input, exception: Exception):
    """Handles exceptions occurring during news extraction process."""

    isBusinessException = isinstance(exception, BusinessException)
    exception_type = "BUSINESS" if isBusinessException else "APPLICATION"
    item.fail(exception_type=exception_type, message=str(exception))
    logger.error(exception)
