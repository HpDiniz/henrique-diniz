from robocorp import workitems
from robocorp.tasks import task

NEWS_JSON_FILE_PATH = "output/news.json"


@task
def produce_news_data():
    """
    Inhuman Insurance, Inc. Artificial Intelligence System automation.
    Produces news data work items.
    """
    payloads = create_work_item_payloads()
    save_work_item_payloads(payloads)


def create_work_item_payloads():
    payloads = []

    payloads.append({
        'search_phrase': 'Carnival',
        'news_category': 'World & Nation',
        'number_of_months': 50,
    })
    payloads.append({
        'search_phrase': 'Bitcoin',
        'news_category': '',
        'number_of_months': 45,
    })
    payloads.append({
        'search_phrase': 'Elon Musk',
        'news_category': '',
        'number_of_months': 100,
    })

    return payloads


def save_work_item_payloads(payloads):
    for payload in payloads:
        variables = dict(news_data=payload)
        workitems.outputs.create(variables)
