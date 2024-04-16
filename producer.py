from robocorp import workitems
from robocorp.tasks import task
from RPA.HTTP import HTTP
from RPA.JSON import JSON
from RPA.Tables import Tables

http = HTTP()
json = JSON()
table = Tables()

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
        'number_of_months': 12,
    })
    payloads.append({
        'search_phrase': 'Bitcoin',
        'news_category': '',
        'number_of_months': 9,
    })
    payloads.append({
        'search_phrase': 'Elon Musk',
        'news_category': '',
        'number_of_months': 1,
    })

    return payloads


def save_work_item_payloads(payloads):
    for payload in payloads:
        variables = dict(news_data=payload)
        workitems.outputs.create(variables)
